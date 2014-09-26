# coding=utf-8
import os
import re
import json
from sys import platform as _platform

import yaml
import requests
from django.db import models
from django.conf import settings
from fabric.context_managers import lcd
from fabric.operations import local
from fabric.api import settings as fabric_settings

from frigg.utils import github_api_request


# sys.path.append(os.path.dirname(__file__))


class BuildResult(models.Model):
    result_log = models.TextField()
    succeeded = models.BooleanField(default=False)
    return_code = models.CharField(max_length=100)

    def get_status(self):
        if self.succeeded:
            return "succeded"
        else:
            return "failed"

    def get_comment_message(self, url):
        if self.succeeded:
            return "All gooodie good\n\n%s" % url
        else:
            return "Be careful.. the tests failed\n\n%s" % url


class Build(models.Model):
    git_repository = models.CharField(max_length=150, verbose_name="git@github.com:owner/repo.git")
    pull_request_id = models.IntegerField(max_length=150, default=0)
    branch = models.CharField(max_length=100, default="master")
    sha = models.CharField(max_length=150)

    result = models.OneToOneField(BuildResult, null=True)

    def get_absolute_url(self):
        return "https://%s/build/%s/" % (settings.SERVER_ADDRESS, self.id)

    def get_pull_request_url(self):
        if self.branch == "master":
            return "https://github.com/%s/%s/" % (self.get_owner(), self.get_name())

        return "https://github.com/%s/%s/pull/%s" % (self.get_owner(),
                                                     self.get_name(),
                                                     self.pull_request_id)

    def get_git_repo_owner_and_name(self):
        rex = "git@github.com:(\w*)/([\w.]*).git"
        match = re.match(rex, self.git_repository)

        return match.group(1), match.group(2)

    def get_owner(self):
        return self.get_git_repo_owner_and_name()[0]

    def get_name(self):
        return self.get_git_repo_owner_and_name()[1]

    def load_settings(self):
        path = os.path.join(self.working_directory(), '.frigg.yml')
        settings = {
            'webhooks': []
        }
        with open(path) as f:
            settings.update(yaml.load(f))
        return settings

    def run_tests(self):
        self._set_commit_status("pending")
        self.add_comment("Running tests.. be patient :)\n\n%s" %
                         self.get_absolute_url())
        build_result = BuildResult.objects.create()
        self.result = build_result
        self.save()
        try:
            self._clone_repo()

            for task in self.load_settings()['tasks']:
                self._run_task(task)
                if not self.result.succeeded:
                    # if one task fails, we do not care about the rest
                    break

        except AttributeError, e:
            self.result.succeeded = False
            self.result.result_log = str(e)
            self.result.save()
            self.add_comment("I was not able to perform the tests.. Sorry. \n "
                             "More information: \n\n %s" % str(e))

        self.add_comment(self.result.get_comment_message(self.get_absolute_url()))
        self._set_commit_status(self.result.get_status())

        for url in self.load_settings()['webhooks']:
            self.send_webhook(url)

    def deploy(self):
        with lcd(self.working_directory()):
            local("./deploy.sh")

    def _clone_repo(self):
        # Cleanup old if exists..
        self._delete_tmp_folder()
        local("mkdir -p %s" % settings.PROJECT_TMP_DIRECTORY)
        local("git clone %s %s" % (self.git_repository, self.working_directory()))

        with lcd(self.working_directory()):
            local("git checkout %s" % self.branch)

    def _run_task(self, task_command):
        options = {
            'pwd': self.working_directory(),
            'command': task_command
        }

        with fabric_settings(warn_only=True):
            with lcd(self.working_directory()):
                if _platform == "darwin":
                    script_command = "script %(pwd)s/frigg_testlog %(command)s"
                else:
                    script_command = "script -c \"%(command)s\" |tee %(pwd)s/frigg_testlog"

                run_result = local(script_command % options)

                self.result.succeeded = run_result.succeeded
                self.result.return_code += "%s," % run_result.return_code

                log = 'Task: %(command)s\n' % options
                log += '------------------------------------\n'

                with file("%(pwd)s/frigg_testlog" % options, "r") as f:
                    log += f.read() + "\n"

                log += '------------------------------------\n'
                log += 'Exited with exit code: %s\n\n' % run_result.return_code
                self.result.result_log += log
                self.result.save()

    def add_comment(self, message):
        if bool(self.load_settings().get('comment', True)):
            owner, repo = self.get_git_repo_owner_and_name()
            url = "%s/%s/commits/%s/comments" % (owner, repo, self.sha)
            github_api_request(url, {'body': message, 'sha': self.sha})

    def _set_commit_status(self, status, description="Done"):
        owner, repo = self.get_git_repo_owner_and_name()

        url = "%s/%s/statuses/%s" % (owner, repo, self.sha)

        data = {'state': status,
                'target_url': 'https://frigg.tind.io',
                'description': description,
                'context': 'build'}

        github_api_request(url, data)

    def _delete_tmp_folder(self):
        if os.path.exists(self.working_directory()):
            local("rm -rf %s" % self.working_directory())

    def testlog(self):
        try:
            with file("%s/frigg_testlog" % self.working_directory(), "r") as f:
                return f.read()
        except IOError:
            return ""

    def send_webhook(self, url):
        return requests.post(url, data=json.dumps({
            'repository': self.git_repository,
            'sha': self.sha,
            'build_url': self.get_absolute_url(),
            'pull_request_id': self.pull_request_id,
            'state': self.result.succeeded,
            'return_code': self.result.return_code
        }))

    def working_directory(self):
        return os.path.join(settings.PROJECT_TMP_DIRECTORY, str(self.id))
