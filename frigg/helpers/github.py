# -*- coding: utf8 -*-
import json

import requests
from django.conf import settings
from frigg.settings import IGNORED_PULL_REQUEST_ACTIONS

from .common import is_retest_comment


def parse_comment_payload(data):
    if is_retest_comment(data['comment']['body']):
        repo_name = data['repository']['name']
        repo_owner = data['repository']['owner']['login']

        repo_url = "git@github.com:%s/%s.git" % (
            repo_owner,
            repo_name
        )

        try:
            pull_request = data['issue']['pull_request']
            pull_request_url = pull_request['url']
            pull_request_id = pull_request_url.split("/")[-1]
        except KeyError:
            pull_request_url = ""
            pull_request_id = ""

        return {
            'repo_url': repo_url,
            'repo_name': repo_name,
            'repo_owner': repo_owner,
            'private': data['repository']['private'],
            'pull_request_id': pull_request_id,
            'pull_request_url': pull_request_url
        }


def parse_pull_request_payload(data):
    # Ignore building pull request if the pull request is being closed
    if data['action'] in IGNORED_PULL_REQUEST_ACTIONS:
        return None

    repo_name = data['repository']['name']
    repo_owner = data['repository']['owner']['login']

    repo_url = "git@github.com:%s/%s.git" % (
        repo_owner,
        repo_name
    )

    return {
        'repo_url': repo_url,
        'repo_name': repo_name,
        'repo_owner': repo_owner,
        'private': data['repository']['private'],
        'pull_request_id': data['number'],
        'branch': data['pull_request']['head']['ref'],
        "sha": data['pull_request']['head']['sha']
    }


def parse_push_payload(data):
    if data['ref'] == "refs/heads/master":
        repo_url = "git@github.com:%s/%s.git" % (
            data['repository']['owner']['name'],
            data['repository']['name']
        )

        return {
            'repo_url': repo_url,
            'repo_name': data['repository']['name'],
            'repo_owner': data['repository']['owner']['name'],
            'private': data['repository']['private'],
            'pull_request_id': 0,
            'branch': 'master',
            "sha": data['after']
        }


def comment_on_commit(build, message):
    if settings.DEBUG or not hasattr(settings, 'GITHUB_ACCESS_TOKEN'):
        return
    url = "%s/%s/commits/%s/comments" % (build.project.owner, build.project.name, build.sha)
    return api_request(url, settings.GITHUB_ACCESS_TOKEN, {'body': message, 'sha': build.sha})


def get_pull_request_url(build):
    if build.branch == "master":
        return "https://github.com/%s/%s/" % (build.project.owner, build.project.name)

    return "https://github.com/%s/%s/pull/%s" % (build.project.owner, build.project.name,
                                                 build.pull_request_id)


def set_commit_status(build, pending=False, error=None):
    if settings.DEBUG:
        return
    url = "%s/%s/statuses/%s" % (build.project.owner, build.project.name, build.sha)
    status, description = _get_status_from_build(build, pending, error)

    return api_request(url, build.project.github_token, {
        'state': status,
        'target_url': build.get_absolute_url(),
        'description': description,
        'context': 'continuous-integration/frigg'
    })


def _get_status_from_build(build, pending, error):
    if pending:
        status = 'pending'
        description = "Frigg started the build."
    else:
        if error is None:
            description = 'The build finished.'
            if build.result.succeeded:
                status = 'success'
            else:
                status = 'failure'
        else:
            status = 'error'
            description = "The build errored: %s" % error

    return status, description


def api_request(url, token, data=None):
    url = "https://api.github.com/repos/%s?access_token=%s" % (url, token)
    if data is None:
        return requests.get(url).text
    else:
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/vnd.github.she-hulk-preview+json'
        }
        return requests.post(url, data=json.dumps(data), headers=headers).text
