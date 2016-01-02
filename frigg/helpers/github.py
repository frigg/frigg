# -*- coding: utf8 -*-
import json

import requests
from django.conf import settings


def get_pull_request_url(build):
    if build.pull_request_id > 0:
        return 'https://github.com/%s/%s/pull/%s' % (build.project.owner, build.project.name,
                                                     build.pull_request_id)

    return 'https://github.com/%s/%s' % (build.project.owner, build.project.name)


def get_commit_url(build):
    return 'https://github.com/%s/%s/commit/%s/' % (
        build.project.owner,
        build.project.name,
        build.sha
    )


def list_members(owner):
    url = 'orgs/{}/members'.format(owner.name)
    data = json.loads(api_request(url, owner.github_token).text)
    print(data)
    return [collaborator['login'] for collaborator in data]


def list_collaborators(project):
    url = 'repos/%s/%s/collaborators' % (project.owner, project.name)
    data = json.loads(api_request(url, project.github_token).text)
    return [collaborator['login'] for collaborator in data]


def set_commit_status(build, pending=False, error=None, context='frigg'):
    if settings.DEBUG or getattr(settings, 'STAGING', False):
        return
    url = "repos/%s/%s/statuses/%s" % (build.project.owner, build.project.name, build.sha)
    if context == 'frigg':
        status, description = _get_status_from_build(build, pending, error)
        target_url = build.get_absolute_url()
    elif context == 'frigg-preview':
        status, description = _get_status_from_deployment(build, pending, error)
        target_url = build.deployment.get_deployment_url()
    else:
        raise RuntimeError('Unknown context')

    return api_request(url, build.project.github_token, {
        'state': status,
        'target_url': target_url,
        'description': description,
        'context': 'continuous-integration/{0}'.format(context)
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


def _get_status_from_deployment(build, pending, error):
    if pending:
        status = 'pending'
        description = 'Frigg started to deploy the preview.'
    else:
        if error is None:
            description = 'Preview is deployed to {0}.'.format(
                build.deployment.get_deployment_url()
            )
            if build.deployment.succeeded:
                status = 'success'
            else:
                status = 'failure'
        else:
            status = 'error'
            description = "The preview deployment errored: %s" % error

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

    print(url)

    if settings.DEBUG:
        print((response.headers.get('X-RateLimit-Remaining')))
    print(response.text)
    return response
