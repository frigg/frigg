# -*- coding: utf8 -*-
import os
import json

from django.conf import settings
from django.test import TestCase
from frigg.builds.models import Build, BuildResult, Project
from frigg.helpers.github import _get_status_from_build

from .github import parse_comment_payload, parse_push_payload, parse_pull_request_payload


class GithubHelpersTestCase(TestCase):
    def setUp(self):
        self.fixtures_path = os.path.join(settings.BASE_DIR, 'helpers/fixtures/github')

    def test_parse_issue_comment_payload(self):
        data = json.load(open(os.path.join(self.fixtures_path, 'issue_comment.json')))
        output = parse_comment_payload(data)

        self.assertEquals(output['repo_url'], 'git@github.com:tind/frigg.git')
        self.assertEquals(output['repo_owner'], 'tind')
        self.assertEquals(output['repo_name'], 'frigg')
        self.assertEquals(output['private'], False)
        self.assertEquals(output['pull_request_id'], '29')

    def test_parse_pull_request_payload(self):
        data = json.load(open(os.path.join(self.fixtures_path, 'pull_request.json')))
        output = parse_pull_request_payload(data)

        self.assertEquals(output['repo_url'], 'git@github.com:tind/frigg.git')
        self.assertEquals(output['repo_owner'], 'tind')
        self.assertEquals(output['repo_name'], 'frigg')
        self.assertEquals(output['private'], False)

    def test_parse_pull_request_payload_labeled(self):
        data = json.load(open(os.path.join(self.fixtures_path, 'pull_request_labeled.json')))
        output = parse_pull_request_payload(data)

        self.assertEqual(output, None)

    def test_parse_pull_request_payload_closed(self):
        data = json.load(open(os.path.join(self.fixtures_path, 'pull_request_closed.json')))
        output = parse_pull_request_payload(data)

        self.assertEqual(output, None)

    def test_parse_push_payload(self):
        data = json.load(open(os.path.join(self.fixtures_path, 'push_master.json')))
        output = parse_push_payload(data)

        self.assertEquals(output['repo_url'], 'git@github.com:tind/frigg.git')
        self.assertEquals(output['repo_owner'], 'tind')
        self.assertEquals(output['repo_name'], 'frigg')
        self.assertEquals(output['branch'], 'master')
        self.assertEquals(output['private'], False)
        self.assertEquals(output['sha'], 'fddd2887efd63196e48fd5d6bc0e62e1bafa0276')

        data = json.load(open(os.path.join(self.fixtures_path, 'push_branch.json')))
        self.assertIsNone(parse_push_payload(data))

    def test__get_status_from_build(self):
        error = RuntimeError()
        project = Project.objects.create(name="TestProject")
        build = Build.objects.create(project=project, build_number=1, branch='master', sha='sha')
        build.result = BuildResult.objects.create(result_log='result', succeeded=True,
                                                  return_code=0)

        status = _get_status_from_build(build, True, None)[0]
        self.assertEqual(status, 'pending')
        status = _get_status_from_build(build, False, None)[0]
        self.assertEqual(status, 'success')
        status = _get_status_from_build(build, False, error)[0]
        self.assertEqual(status, 'error')
        build.result.succeeded = False
        build.result.return_code = 1
        build.result.save()
        status = _get_status_from_build(build, False, None)[0]
        self.assertEqual(status, 'failure')
