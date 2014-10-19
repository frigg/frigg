# coding=utf-8
import os
import json
import logging
import threading
import traceback

import yaml
import requests
from django.db import models
from django.conf import settings
from django.utils.functional import cached_property
from django.core.urlresolvers import reverse
from fabric.context_managers import lcd
from fabric.operations import local
from fabric.api import settings as fabric_settings
from social_auth.db.django_models import UserSocialAuth

from frigg.helpers import github
from .managers import ProjectManager
from .helpers import detect_test_runners


logger = logging.getLogger("frigg_build_logger")


class Project(models.Model):
    name = models.CharField(max_length=100, blank=True)
    owner = models.CharField(max_length=100, blank=True)
    git_repository = models.CharField(max_length=150)
    average_time = models.IntegerField(null=True)
    private = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             help_text='A user with access to the repository.')

    objects = ProjectManager()

    def __unicode__(self):
        return "%(owner)s / %(name)s " % self.__dict__

    @property
    def github_token(self):
        try:
            token = UserSocialAuth.objects.get(user=self.user,
                                               provider='github').extra_data['access_token']
        except UserSocialAuth.DoesNotExist:
            token = getattr(settings, 'GITHUB_ACCESS_TOKEN', ':')
        return token

    @property
    def clone_url(self):
        if self.private:
            return "https://%s@github.com/%s/%s" % (self.github_token, self.owner, self.name)
        else:
            return "https://github.com/%s/%s" % (self.owner, self.name)

    @property
    def last_build_number(self):
        try:
            return self.builds.all().order_by('-build_number')[0].build_number
        except IndexError:
            return 0

    @property
    def working_directory(self):
        return os.path.join(settings.PROJECT_TMP_DIRECTORY, self.owner, self.name)

    def start_build(self, data):
        build = Build.objects.create(
            project=self,
            build_number=self.last_build_number + 1,
            pull_request_id=data['pull_request_id'],
            branch=data['branch'],
            sha=data["sha"]
        )

        t = threading.Thread(target=build.run_tests)
        t.setDaemon(True)
        t.start()
        return build

    @classmethod
    def token_for_url(cls, repo_url):
        try:
            project = Project.objects.get(git_repository=repo_url)
            token = project.github_token
        except cls.DoesNotExist:
            token = getattr(settings, 'GITHUB_ACCESS_TOKEN', ':')
        return token


class Build(models.Model):
    project = models.ForeignKey(Project, related_name='builds', null=True)
    build_number = models.IntegerField(db_index=True)
    pull_request_id = models.IntegerField(max_length=150, default=0)
    branch = models.CharField(max_length=100, default="master")
    sha = models.CharField(max_length=150)

    class Meta:
        unique_together = ('project', 'build_number')

    def __unicode__(self):
        return "%s / %s " % (self.project, self.branch)

    def get_absolute_url(self):
        return "https://%s%s" % (
            settings.SERVER_ADDRESS,
            reverse('view_build', args=[self.project.owner, self.project.name, self.build_number])
        )

    def get_pull_request_url(self):
        return github.get_pull_request_url(self)

    @property
    def color(self):
        if self.result is None:
            return 'orange'
        if self.result.succeeded:
            return 'green'
        return 'red'

    @cached_property
    def settings(self):
        path = os.path.join(self.working_directory, '.frigg.yml')
        # Default value for project .frigg.yml
        settings = {
            'webhooks': [],
            'comment': False
        }

        try:
            with open(path) as f:
                settings.update(yaml.load(f))
        except IOError:
            settings['tasks'] = detect_test_runners(self)
        return settings

    def run_tests(self):
        github.set_commit_status(self, pending=True)
        BuildResult.objects.create(build=self)

        if not self._clone_repo():
            return github.set_commit_status(self, error='Access denied')

        self.add_comment("Running tests.. be patient :)\n\n%s" %
                         self.get_absolute_url())
        try:

            for task in self.settings['tasks']:
                self._run_task(task)
                if not self.result.succeeded:
                    # if one task fails, we do not care about the rest
                    break

            github.set_commit_status(self)
            self.add_comment(self.result.get_comment_message(self.get_absolute_url()))

        except AttributeError, e:
            self.result.succeeded = False
            self.result.result_log = str(e)
            self.result.save()
            github.set_commit_status(self, error=e)
            self.add_comment("I was not able to perform the tests.. Sorry. \n "
                             "More information: \n\n %s" % str(e))
        finally:
            if not settings.DEBUG:
                self._delete_tmp_folder()
            for url in self.settings['webhooks']:
                self.send_webhook(url)

    def deploy(self):
        with lcd(self.working_directory):
            local("./deploy.sh")

    def _clone_repo(self, depth=1):
        # Cleanup old if exists..
        self._delete_tmp_folder()
        local("mkdir -p %s" % settings.PROJECT_TMP_DIRECTORY)
        with fabric_settings(warn_only=True):
            clone = local("git clone --depth=%s --branch=%s %s %s" % (
                depth,
                self.branch,
                self.project.clone_url,
                self.working_directory
            ), capture=True)
            if not clone.succeeded:
                message = "Access denied to %s/%s" % (self.project.owner, self.project.name)
                self.result.succeeded = False
                self.result.return_code = 128
                self.result.result_log = message
                self.result.save()
                logger.error(message)
            return clone.succeeded

    def _run_task(self, task_command):
        with fabric_settings(warn_only=True):
            with lcd(self.working_directory):
                run_result = local(task_command, capture=True)

                self.result.succeeded = run_result.succeeded
                self.result.return_code = "%s,%s," % (self.result.return_code,
                                                      run_result.return_code)

                log = 'Task: {0}\n'.format(task_command)
                log += '------------------------------------\n'
                log += run_result
                log += '------------------------------------\n'
                log += 'Exited with exit code: %s\n\n' % run_result.return_code

                self.result.result_log += log
                self.result.save()

    def add_comment(self, message):
        if bool(self.settings.get('comment', True)):
            github.comment_on_commit(self, message)

    def _delete_tmp_folder(self):
        if os.path.exists(self.working_directory):
            result = local("rm -rf %s" % self.working_directory, capture=True)
            if not result.succeeded:
                logger.error('Could not delete folder %s\n%s' % (self.working_directory, result))

    def testlog(self):
        try:
            with file("%s/frigg_testlog" % self.working_directory, "r") as f:
                return f.read()
        except IOError:
            logger.error(traceback.format_exc())
            return ""

    def send_webhook(self, url):
        return requests.post(url, data=json.dumps({
            'repository': self.project.git_repository,
            'sha': self.sha,
            'build_url': self.get_absolute_url(),
            'pull_request_id': self.pull_request_id,
            'state': self.result.succeeded,
            'return_code': self.result.return_code
        }))

    @cached_property
    def working_directory(self):
        return os.path.join(self.project.working_directory, str(self.id))


class BuildResult(models.Model):
    build = models.OneToOneField(Build, related_name='result')
    result_log = models.TextField()
    succeeded = models.BooleanField(default=False)
    return_code = models.CharField(max_length=100)

    def __unicode__(self):
        return "%s - %s" % (self.build, self.build.build_number)

    def get_comment_message(self, url):
        if self.succeeded:
            return "All gooodie good\n\n%s" % url
        else:
            return "Be careful.. the tests failed\n\n%s" % url
