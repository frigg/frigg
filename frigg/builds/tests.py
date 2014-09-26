# coding=utf-8
from django.test import TestCase
from frigg.builds.models import Build


class SimpleTest(TestCase):
    def test_parse_github_repo(self):
        project = Build.objects.create(git_repository="git@github.com:tind/balder.git",
                                       pull_request_id=1, branch="master")

        self.assertEqual(project.get_git_repo_owner_and_name()[0], "tind")
        self.assertEqual(project.get_git_repo_owner_and_name()[1], "balder")
