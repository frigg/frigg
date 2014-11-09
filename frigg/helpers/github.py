# -*- coding: utf8 -*-
import json
import re

import requests
from django.conf import settings

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
    if 'action' in data and data['action'] in settings.IGNORED_PULL_REQUEST_ACTIONS:
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
    url = "repos/%s/%s/commits/%s/comments" % (build.project.owner, build.project.name, build.sha)
    return api_request(url, settings.GITHUB_ACCESS_TOKEN, {'body': message, 'sha': build.sha})


def get_pull_request_url(build):
    if build.branch == "master":
        return "https://github.com/%s/%s/" % (build.project.owner, build.project.name)

    return "https://github.com/%s/%s/pull/%s" % (build.project.owner, build.project.name,
                                                 build.pull_request_id)


def get_commit_url(build):
    return 'https://github.com/%s/%s/commit/%s/' % (
        build.project.owner,
        build.project.name,
        build.sha
    )


def list_collaborators(project):
    url = 'repos/%s/%s/collaborators' % (project.owner, project.name)
    data = json.loads(api_request(url, project.github_token))
    return [collaborator['login'] for collaborator in data]


def set_commit_status(build, pending=False, error=None):
    if settings.DEBUG:
        return
    url = "repos/%s/%s/statuses/%s" % (build.project.owner, build.project.name, build.sha)
    status, description = _get_status_from_build(build, pending, error)

    return api_request(url, build.project.github_token, {
        'state': status,
        'target_url': build.get_absolute_url(),
        'description': description,
        'context': 'continuous-integration/frigg'
    })


def update_repo_permissions(user):
    from frigg.builds.models import Project
    repos = list_user_repos(user)

    for org in list_organization(user):
        repos += list_organization_repos(user.github_token, org['login'])

    for repo in repos:
        try:
            project = Project.objects.get(owner=repo['owner']['login'], name=repo['name'])
            project.members.add(user)
        except Project.DoesNotExist:
            pass


def list_user_repos(user):
    page = 1
    output = []
    response = api_request('user/repos', user.github_token)
    output += json.loads(response.text)
    while response.headers.get('link') and 'next' in response.headers.get('link'):
        page += 1
        response = api_request('user/repos', user.github_token, page=page)
        output += json.loads(response.text)
    return output


def list_organization(user):
    return json.loads(api_request('user/orgs', user.github_token).text)


def list_organization_repos(token, org):
    page = 1
    output = []
    response = api_request('orgs/%s/repos' % org, token)
    output += json.loads(response.text)
    while response.headers.get('link') and 'next' in response.headers.get('link'):
        page += 1
        response = api_request('orgs/%s/repos' % org, token, page=page)
        output += json.loads(response.text)
    return output


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


def api_request(url, token, data=None, page=None):
    url = "https://api.github.com/%s?access_token=%s" % (url, token)
    if page:
        url += '&page=%s' % page
    if data is None:
        response = requests.get(url)
    else:
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/vnd.github.she-hulk-preview+json'
        }
        response = requests.post(url, data=json.dumps(data), headers=headers)

    if settings.DEBUG:
        print(response.headers.get('X-RateLimit-Remaining'))

    return response