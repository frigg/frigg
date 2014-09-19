# coding=utf-8
import json
import threading
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from frigg.builds.models import Build
from frigg.utils import github_api_get_request


@login_required
def overview(request):
    return render(request, "builds/overview.html", {'builds': Build.objects.all().order_by("-id")})


@login_required
def build(request, build_id):
    try:
        build = Build.objects.get(id=build_id)
        return render(request, "builds/build.html", {'build': build})

    except Build.DoesNotExist:
        raise Http404


def build_pull_request(data):
    repo_url = "git@github.com:%s/%s.git" % (data['repo_owner'], data['repo_name'])

    build = Build.objects.create(git_repository=repo_url,
                                 pull_request_id=data['pull_request_id'],
                                 branch=data['branch'],
                                 sha=data["sha"])

    t = threading.Thread(target=build.run_tests)
    t.setDaemon(True)
    t.start()


@login_required
def deploy_master_branch(request, build_id):
    build = Build.objects.get(id=build_id)
    build.deploy()

    return HttpResponse("Deployed")


@csrf_exempt
def github_webhook(request):
    try:
        event = request.META['HTTP_X_GITHUB_EVENT']
    except KeyError:
        return HttpResponse("Missing HTTP_X_GITHUB_EVENT")

    if event == "issue_comment":
        data = json.loads(request.body)

        if data['comment']['body'] == "retest now please":

            url = data['issue']['pull_request']['url'][29:]
            pr_data = json.loads(github_api_get_request(url))

            pull_request = {'repo_name': pr_data['head']['repo']['name'],
                            'repo_owner': pr_data['head']['repo']['owner']['login'],
                            'pull_request_id': pr_data['number'],
                            'branch': pr_data['head']['ref'],
                            "sha": pr_data['head']['sha']}

            build_pull_request(pull_request)

    elif event == "pull_request":

        data = json.loads(request.body)

        # Do nothing if the pull request is being closed
        if data['action'] == "closed":
            return

        pull_request = {'repo_name': data['repository']['name'],
                        'repo_owner': data['repository']['owner']['login'],
                        'pull_request_id': data['number'],
                        'branch': data['pull_request']['head']['ref'],
                        "sha": data['pull_request']['head']['sha']}

        build_pull_request(pull_request)

    # If someone pushed directly to master.. lets test it anyway
    elif event == "push":

        data = json.loads(request.body)

        if data['ref'] == "refs/heads/master":
            pull_request = {'repo_name': data['repository']['name'],
                            'repo_owner': data['repository']['owner']['name'],
                            'pull_request_id': 0,
                            'branch': 'master',
                            "sha": data['after']}

            build_pull_request(pull_request)

    else:
        return HttpResponse("Do nothing :)")

    return HttpResponse(event)