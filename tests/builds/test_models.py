# -*- coding: utf8 -*-
import json
from datetime import datetime, timedelta
from unittest import mock

import redis
import responses
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import get_current_timezone, now
from mockredis import mock_redis_client

from frigg.authentication.models import User
from frigg.builds.models import Build, BuildResult, Project

r = redis.Redis(**settings.REDIS_SETTINGS)


class ProjectTestCase(TestCase):
    fixtures = ['frigg/builds/fixtures/users.json']

    def test___str__(self):
        project = Project.objects.create(owner='frigg', name='frigg-worker')
        self.assertEqual(str(project), 'frigg / frigg-worker')

    def test_clone_url_public(self):
        project = Project(owner='frigg', name='frigg-worker', private=False)
        self.assertEqual(project.clone_url, 'https://github.com/frigg/frigg-worker.git')

    @mock.patch('frigg.builds.models.Project.github_token', '')
    def test_clone_url_private(self):
        project = Project(owner='frigg', name='chewie', private=True)
        self.assertEqual(project.clone_url, 'https://@github.com/frigg/chewie.git')

    @mock.patch('frigg.builds.models.Project.github_token', '')
    def test_clone_url_ssh(self):
        project = Project(owner='frigg', name='chewie', should_clone_with_ssh=True)
        self.assertEqual(project.clone_url, 'git@github.com:frigg/chewie.git')

    def test_last_build_number(self):
        project = Project.objects.create(owner='frigg', name='frigg-worker', private=False)
        self.assertEqual(project.last_build_number, 0)
        Build.objects.create(project=project, build_number=42)
        self.assertEqual(project.last_build_number, 42)

    def test_auto_approval(self):
        project = Project.objects.create(owner='frigg', name='frigg')
        self.assertTrue(project.approved)

    @mock.patch('frigg.helpers.github.list_collaborators', lambda x: ['dumbledore'])
    def test_update_members(self):
        project = Project.objects.create(owner='frigg', name='frigg-worker', private=False)
        project.update_members()
        self.assertEqual(project.members.all().count(), 1)

    def test_start(self):
        project = Project.objects.create(owner='frigg', name='frigg')
        build = project.start_build({
            'branch': 'b',
            'sha': 's',
            'author': 'dumbledore',
            'pull_request_id': 0,
            'message': '',
        })
        self.assertEqual(build.branch, 'b')
        self.assertEqual(build.sha, 's')
        self.assertEqual(build.author, 'dumbledore')
        self.assertEqual(build.pull_request_id, 0)
        self.assertEqual(build.build_number, 1)
        self.assertEqual(project.last_build_number, 1)

    @mock.patch('frigg.builds.models.Build.start')
    def test_start_pull_request_with_earlier_build(self, mock_start):
        data = {
            'branch': 'b',
            'sha': 's',
            'author': 'dumbledore',
            'pull_request_id': 0,
            'message': '',
        }
        project = Project.objects.create(owner='frigg', name='frigg')
        project.start_build(data)
        self.assertEqual(project.builds.count(), 1)
        self.assertEqual(project.last_build_number, 1)
        data['pull_request_id'] = 1
        self.assertEqual(project.builds.count(), 1)
        data['pull_request_id'] = 1
        build = project.start_build(data)
        self.assertEqual(build.branch, 'b')
        self.assertEqual(build.sha, 's')
        self.assertEqual(build.author, 'dumbledore')
        self.assertEqual(build.pull_request_id, 1)
        self.assertEqual(build.build_number, 1)
        self.assertEqual(project.last_build_number, 1)

    def test_average_time(self):
        project = Project.objects.create(owner='frigg', name='frigg-worker', private=False)
        build_options = dict(project=project, build_number=1,
                             start_time=datetime(2015, 5, 5, 5, 5, tzinfo=get_current_timezone()),
                             end_time=datetime(2015, 5, 5, 5, 15, tzinfo=get_current_timezone()))
        builds = [Build.objects.create(**build_options)]
        build_options = dict(project=project, build_number=2,
                             start_time=datetime(2015, 5, 5, 5, 5, tzinfo=get_current_timezone()),
                             end_time=datetime(2015, 5, 5, 5, 25, tzinfo=get_current_timezone()))
        builds += [Build.objects.create(**build_options)]
        self.assertEqual(project.average_time, timedelta(minutes=15))

    def test_number_of_members(self):
        project = Project.objects.create(owner='frigg', name='frigg-worker', private=False)
        self.assertEqual(project.number_of_members, 0)
        project.members.add(User.objects.get(pk=1))
        self.assertEqual(project.number_of_members, 1)

    @mock.patch('frigg.builds.models.get_badge')
    def test_get_badge_should_call_badge_with_last_build(self, mock_get_badge):
        project = Project.objects.create(owner='frigg', name='frigg-worker', private=False)
        build = Build.objects.create(project=project)
        BuildResult.objects.create(build=build, succeeded=True)
        self.assertIsNotNone(project.get_badge())
        mock_get_badge.assert_called_once_with(True)

    @mock.patch('frigg.builds.models.get_unknown_badge')
    def test_get_badge_should_call_unknown_badge_if_no_build(self, mock_get_unknown_badge):
        project = Project.objects.create(owner='frigg', name='frigg-worker', private=False)
        self.assertIsNotNone(project.get_badge())
        mock_get_unknown_badge.assert_called_once_with('build')

    @mock.patch('frigg.builds.models.get_coverage_badge')
    def test_get_coverage_badge_should_call_coverage_badge_with_last_build(self, mock_get_badge):
        project = Project.objects.create(owner='frigg', name='frigg-worker', private=False)
        build = Build.objects.create(project=project)
        BuildResult.objects.create(build=build, succeeded=True, coverage=98)
        self.assertIsNotNone(project.get_coverage_badge())
        mock_get_badge.assert_called_once_with(98)

    @mock.patch('frigg.builds.models.get_unknown_badge')
    def test_get_coverage_badge_should_call_unknown_badge_if_no_buildt(self, mock_get_unknown):
        project = Project.objects.create(owner='frigg', name='frigg-worker', private=False)
        self.assertIsNotNone(project.get_coverage_badge())
        mock_get_unknown.assert_called_once_with('coverage')


class BuildTestCase(TestCase):
    fixtures = ['frigg/builds/fixtures/users.json']

    def setUp(self):
        r.flushall()
        self.project = Project.objects.create(owner='frigg', name='frigg-worker', approved=True)

    def test___str__(self):
        build = Build.objects.create(project=self.project, branch='master', build_number=1)
        self.assertEqual(str(build), 'frigg / frigg-worker / master #1')

    @mock.patch('frigg.builds.models.Project.github_token', 'token')
    def test_queue_object(self):
        build = Build.objects.create(project=self.project, branch='master', sha='s', build_number=1)
        obj = build.queue_object
        self.assertEqual(obj['id'], build.pk)
        self.assertEqual(obj['branch'], build.branch)
        self.assertEqual(obj['sha'], build.sha)
        self.assertEqual(obj['image'], settings.DEFAULT_BUILD_IMAGE)
        self.assertEqual(obj['clone_url'], build.project.clone_url)
        self.assertEqual(obj['owner'], build.project.owner)
        self.assertEqual(obj['name'], build.project.name)
        self.assertEqual(obj['gh_token'], 'token')
        self.assertFalse('pull_request_id' in obj)
        build.pull_request_id = 42
        obj = build.queue_object
        self.assertEqual(obj['pull_request_id'], 42)

    def test_queue_object_have_environment_variables(self):
        self.project.environment_variables.create(key='V', value=42, is_secret=False)
        build = Build.objects.create(project=self.project, branch='master', sha='s', build_number=1)
        obj = build.queue_object
        assert obj['environment_variables']['V'] == '42'
        assert 'V' not in obj['secrets']

    def test_queue_object_have_secrets_when_no_pull_request(self):
        self.project.environment_variables.create(key='V', value=40, is_secret=True)
        build = Build.objects.create(project=self.project, branch='master', sha='s', build_number=1)
        obj = build.queue_object
        assert obj['secrets']['V'] == '40'
        assert 'V' not in obj['environment_variables']

    def test_queue_object_not_have_secrets_when_no_pull_request_and_custom_branch(self):
        self.project.environment_variables.create(key='V', value=40, is_secret=True)
        build = Build.objects.create(project=self.project, branch='custom', sha='s', build_number=1)
        obj = build.queue_object
        assert 'V' not in obj['secrets']
        assert 'V' not in obj['environment_variables']

    def test_queue_object_not_have_secrets_when_pull_request(self):
        self.project.environment_variables.create(key='V', value=40, is_secret=True)
        build = Build.objects.create(
            project=self.project,
            branch='master',
            sha='s',
            build_number=1,
            pull_request_id=2
        )
        obj = build.queue_object
        assert 'V' not in obj['secrets']

    def test_queue_set_custom_image(self):
        custom_docker_image = 'frigg/frigg-test-dind'
        project = Project.objects.create(image=custom_docker_image)
        build = Build.objects.create(project=project)
        obj = build.queue_object
        self.assertEqual(obj['id'], build.pk)
        self.assertEqual(obj['image'], custom_docker_image)

    def test_color(self):
        build = Build.objects.create(project=self.project, branch='master', build_number=1)
        self.assertEqual(build.color, 'orange')
        result = BuildResult.objects.create(build=build, succeeded=True, result_log=[])
        self.assertEqual(build.color, 'green')
        result.still_running = True
        self.assertEqual(build.color, 'orange')
        result.still_running = False
        result.succeeded = False
        self.assertEqual(build.color, 'red')
        result.result_log = [{'task': ''}]
        self.assertEqual(build.color, 'gray')

    @responses.activate
    def test_send_webhook(self):
        responses.add(
            responses.POST,
            'http://w.frigg.io',
            body='Ok',
            content_type='application/json'
        )
        build = Build.objects.create(project=self.project, branch='master', build_number=1)
        BuildResult.objects.create(build=build, succeeded=True)
        response = build.send_webhook('http://w.frigg.io')
        request = json.loads(response.request.body)
        self.assertEqual(request['sha'], build.sha)
        self.assertEqual(request['build_url'], build.get_absolute_url())
        self.assertEqual(request['state'], build.result.succeeded)

    @mock.patch('frigg.helpers.github.set_commit_status')
    @mock.patch('redis.Redis', mock_redis_client)
    def test_start(self, mock_set_commit_status):
        build = Build.objects.create(project=self.project, branch='master', build_number=1)
        BuildResult.objects.create(build=build, succeeded=True)
        build.start()
        self.assertEqual(BuildResult.objects.all().count(), 0)
        self.assertTrue(mock_set_commit_status.called)

    @mock.patch('frigg.helpers.github.set_commit_status')
    @mock.patch('redis.Redis', mock_redis_client)
    def test_start_restart_should_not_have_end_time(self, mock_set_commit_status):
        build = Build.objects.create(project=self.project, branch='master', build_number=1,
                                     end_time=now())
        build.start()
        build = Build.objects.get(project=self.project, build_number=1)
        self.assertIsNone(build.end_time)
        self.assertTrue(mock_set_commit_status.called)

    @mock.patch('frigg.builds.models.BuildResult.create_not_approved')
    @mock.patch('redis.Redis', mock_redis_client)
    def test_start_not_approved(self, mock_create_not_approved):
        project = Project.objects.create(owner='tind', name='frigg', approved=False)
        build = Build.objects.create(project=project, branch='master', build_number=1)
        build.start()
        self.assertTrue(mock_create_not_approved.called)

    @mock.patch('frigg.builds.models.Build.start')
    def test_restart_should_start_if_not_in_queue(self, mock_start):
        project = Project.objects.create(owner='tind', name='frigg', approved=False)
        build = Build.objects.create(project=project, branch='master', build_number=1)
        build.start()
        r.rpop(project.queue_name)
        assert r.llen(project.queue_name) == 0
        build.restart()
        assert mock_start.called

    @mock.patch('frigg.builds.models.Build.start')
    def test_restart_should_not_start_if_already_in_queue(self, mock_start):
        project = Project.objects.create(owner='tind', name='frigg', approved=False)
        build = Build.objects.create(project=project, branch='master', build_number=1)
        r.lpush(project.queue_name, json.dumps(build.queue_object))
        build.restart()
        assert not mock_start.called

    def test_has_timed_out(self):
        project = Project.objects.create(owner='frigg', name='frigg')
        build = Build.objects.create(project=project, build_number=1,
                                     start_time=now() - timedelta(minutes=61))
        self.assertTrue(build.has_timed_out())
        build.start_time = now()
        self.assertFalse(build.has_timed_out())
        with mock.patch('frigg.builds.models.Project.average_time', timedelta(seconds=120)):
            self.assertFalse(build.has_timed_out())
            build.start_time = now() - timedelta(seconds=60)
            self.assertFalse(build.has_timed_out())
            build.start_time = now() - timedelta(seconds=400)
            self.assertTrue(build.has_timed_out())

    def test_author_user(self):
        user = get_user_model().objects.get(pk=1)
        build = Build(
            project=self.project,
            branch='master',
            build_number=1,
            author=user.username
        )
        self.assertEqual(build.author_user, user)
        build.author = 'i'
        self.assertIsNone(build.author_user)

    def test_short_message(self):
        build = Build(
            project=self.project,
            branch='master',
            build_number=1,
            message='Multi\nLine\nMessage'
        )
        self.assertEqual(build.short_message, 'Multi')
        build = Build(
            project=self.project,
            branch='master',
            build_number=1,
            message='Single line message'
        )
        self.assertEqual(build.short_message, 'Single line message')

    def test_rendered_message(self):
        build = Build(
            project=self.project,
            branch='master',
            build_number=1,
            message='Single **line** message'
        )
        self.assertEqual(build.rendered_message, '<p>Single <strong>line</strong> message</p>')

    @mock.patch('frigg.builds.models.Build.send_webhook')
    @mock.patch('frigg.helpers.github.set_commit_status')
    def test_handle_worker_report(self, mock_set_commit_status, mock_send_webhook):
        build = Build.objects.create(
            project=self.project,
            branch='master',
            build_number=1,
        )
        build.handle_worker_report({
            'sha': 'superbhash',
            'clone_url': 'https://github.com/frigg/frigg-worker.git',
            'name': 'frigg-worker',
            'branch': 'master',
            'owner': 'frigg',
            'id': 1,
            'results': [
                {'task': 'make test', 'return_code': 0, 'succeeded': True, 'log': 'log'},
                {'task': 'make test'}
            ],
            'webhooks': ['http://example.com']
        })
        self.assertIsNotNone(Build.objects.get(pk=build.id).end_time)
        mock_set_commit_status.assert_called_once_with(build)
        mock_send_webhook.assert_called_once_with('http://example.com')

    @mock.patch('frigg.builds.models.Build.send_webhook')
    @mock.patch('frigg.helpers.github.set_commit_status')
    def test_handle_worker_host(self, mock_set_commit_status, mock_send_webhook):
        build = Build.objects.create(
            project=self.project,
            branch='master',
            build_number=1,
        )
        build.handle_worker_report({
            'sha': 'superbhash',
            'clone_url': 'https://github.com/frigg/frigg-worker.git',
            'name': 'frigg-worker',
            'branch': 'master',
            'owner': 'frigg',
            'id': 1,
            'results': [
                {'task': 'make test', 'return_code': 0, 'succeeded': True, 'log': 'log'},
                {'task': 'make test'}
            ],
            'webhooks': ['http://example.com']
        })
        self.assertIsNotNone(Build.objects.get(pk=build.id).end_time)
        mock_set_commit_status.assert_called_once_with(build)
        mock_send_webhook.assert_called_once_with('http://example.com')

    @mock.patch('frigg.builds.models.Build.send_webhook')
    @mock.patch('frigg.helpers.github.set_commit_status')
    def test_handle_worker_report_still_running(self, mock_set_commit_status, mock_send_webhook):
        build = Build.objects.create(
            project=self.project,
            branch='master',
            build_number=1,
        )
        build.handle_worker_report({
            'sha': 'superbhash',
            'clone_url': 'https://github.com/frigg/frigg-worker.git',
            'name': 'frigg-worker',
            'branch': 'master',
            'owner': 'frigg',
            'worker_host': 'albus.frigg.io',
            'finished': False,
            'id': 1,
            'results': [
                {'task': 'make test', 'return_code': 0, 'succeeded': True, 'log': 'log'},
                {'task': 'flake8', 'pending': True},
                {'task': 'make test'}
            ],
            'webhooks': ['http://example.com']
        })
        self.assertIsNone(Build.objects.get(pk=build.id).end_time)
        self.assertEqual(build.result.worker_host, 'albus.frigg.io')

    @mock.patch('frigg.builds.models.Project.average_time', timedelta(minutes=10))
    def test_estimated_finish_time(self):
        build = Build(
            project=self.project,
        )
        self.assertEqual(build.estimated_finish_time, None)
        build.start_time = now()
        self.assertEqual(build.estimated_finish_time.day, (now() + timedelta(minutes=10)).day)
        self.assertEqual(build.estimated_finish_time.hour, (now() + timedelta(minutes=10)).hour)
        self.assertEqual(build.estimated_finish_time.minute, (now() + timedelta(minutes=10)).minute)

    @mock.patch('frigg.deployments.models.PRDeployment.start')
    def test_initiate_deployment_with_specified_image(self, mock_deployment_start):
        start_time = datetime(2012, 12, 12, tzinfo=get_current_timezone())

        b1 = Build.objects.create(project=self.project, branch='master',
                                  build_number=4, start_time=start_time)

        deployment = b1.initiate_deployment({'image': 'frigg/super-image'})
        self.assertEqual(deployment.image, 'frigg/super-image')

        self.assertTrue(mock_deployment_start.called_once)

    @mock.patch('frigg.deployments.models.PRDeployment.start')
    def test_initiate_deployment_without_specified_image(self, mock_deployment_start):
        start_time = datetime(2012, 12, 12, tzinfo=get_current_timezone())

        b1 = Build.objects.create(project=self.project, branch='master',
                                  build_number=4, start_time=start_time)

        deployment = b1.initiate_deployment({})
        self.assertEqual(deployment.image, settings.FRIGG_PREVIEW_IMAGE)

        self.assertTrue(mock_deployment_start.called_once)

    def test_delete_logs_should_remove_logs(self):
        build = Build.objects.create(project=self.project, branch='master', build_number=4)
        result = BuildResult.objects.create(
            build=build,
            setup_log=[{"item": "something"}],
            service_log=[{"item": "something"}],
            result_log=[{"item": "something"}],
            after_log=[{"item": "something"}],
        )

        build.delete_logs()

        result = BuildResult.objects.get(pk=result.pk)
        self.assertEqual(result.setup_log, [])
        self.assertEqual(result.service_tasks, [])
        self.assertEqual(result.result_log, [])
        self.assertEqual(result.after_tasks, [])

    class BuildResultTestCase(TestCase):
        def setUp(self):
            self.project = Project.objects.create(owner='frigg', name='frigg-worker')
            self.build = Build.objects.create(project=self.project, branch='master', build_number=1)

        def test___str__(self):
            result = BuildResult.objects.create(build=self.build)
            self.assertEqual(str(result), 'frigg / frigg-worker / master #1')

        def test_evaluate_results(self):
            self.assertTrue(BuildResult.evaluate_results([{'succeeded': True}]))
            self.assertTrue(BuildResult.evaluate_results([{'succeeded': True}, {}]))
            self.assertFalse(BuildResult.evaluate_results([{'succeeded': True}, {'succeeded': False}]))
            self.assertFalse(BuildResult.evaluate_results([{'succeeded': False}, {'succeeded': True}]))
            self.assertFalse(BuildResult.evaluate_results([{'succeeded': False}, {}]))

        def test_create_not_approved(self):
            result = BuildResult.create_not_approved(self.build)
            self.assertEqual(result.build_id, self.build.pk)
            self.assertFalse(result.succeeded)
            assert result.tasks[0]['error'] == 'This project is not approved.'
            assert result.setup_tasks == []
            assert result.service_tasks == []

        def test_create_from_worker_payload(self):
            BuildResult.create_from_worker_payload(self.build, {
                'sha': 'superbhash',
                'clone_url': 'https://github.com/frigg/frigg-worker.git',
                'name': 'frigg-worker',
                'branch': 'master',
                'owner': 'frigg',
                'worker_host': 'albus.frigg.io',
                'finished': False,
                'id': 1,
                'results': [
                    {'task': 'make test', 'return_code': 0, 'succeeded': True, 'log': 'log'},
                    {'task': 'flake8', 'pending': True},
                    {'task': 'make test'}
                ],
                'service_results': [
                    {'task': 'service postgresql start', 'return_code': 0, 'succeeded': True,
                     'log': 'log'},
                ],
                'setup_results': [
                    {'task': 'make', 'return_code': 0, 'succeeded': True, 'log': 'log'},
                ],
                'after_results': [
                    {'task': 'after', 'return_code': 0, 'succeeded': True, 'log': 'log'},
                ],
                'webhooks': ['http://example.com']
            })

            assert self.build.result.worker_host == 'albus.frigg.io'
            assert self.build.result.still_running
            assert isinstance(self.build.result.tasks, list)
            assert isinstance(self.build.result.setup_log, list)
            assert isinstance(self.build.result.service_tasks, list)
            assert isinstance(self.build.result.after_tasks, list)

        def test_create_from_worker_payload_without_optional_results(self):
            BuildResult.create_from_worker_payload(self.build, {
                'sha': 'superbhash',
                'clone_url': 'https://github.com/frigg/frigg-worker.git',
                'name': 'frigg-worker',
                'branch': 'master',
                'owner': 'frigg',
                'worker_host': 'albus.frigg.io',
                'finished': False,
                'id': 1,
                'results': [
                    {'task': 'make test', 'return_code': 0, 'succeeded': True, 'log': 'log'},
                    {'task': 'flake8', 'pending': True},
                    {'task': 'make test'}
                ],
                'webhooks': ['http://example.com']
            })

            assert isinstance(self.build.result.tasks, list)
            assert isinstance(self.build.result.setup_log, list)
            assert isinstance(self.build.result.service_tasks, list)
            assert isinstance(self.build.result.after_tasks, list)

        def test_tasks(self):
            data = [
                {'task': 'tox', 'log': '{}', 'return_code': 0},
                {'task': 'tox', 'log': 'tested all the stuff\n1!"#$%&/()=?', 'return_code': 11},
                {'task': 'tox', 'return_log': 'fail', 'return_code': 'd'}
            ]
            result = BuildResult.objects.create(
                build=self.build,
                result_log=data
            )
            self.assertEqual(len(result.tasks), 3)
            self.assertEqual(result.tasks, data)

        def test_service_tasks(self):
            data = [
                {'task': 'tox', 'log': '{}', 'return_code': 0},
                {'task': 'tox', 'log': 'tested all the stuff\n1!"#$%&/()=?', 'return_code': 11},
                {'task': 'tox', 'return_log': 'fail', 'return_code': 'd'}
            ]
            result = BuildResult.objects.create(
                build=self.build,
                service_log=data
            )
            self.assertEqual(len(result.service_tasks), 3)
            self.assertEqual(result.service_tasks, data)

        def test_setup_tasks(self):
            data = [
                {'task': 'tox', 'log': '{}', 'return_code': 0},
                {'task': 'tox', 'log': 'tested all the stuff\n1!"#$%&/()=?', 'return_code': 11},
                {'task': 'tox', 'return_log': 'fail', 'return_code': 'd'}
            ]
            result = BuildResult.objects.create(
                build=self.build,
                setup_log=data
            )
            self.assertEqual(len(result.setup_tasks), 3)
            self.assertEqual(result.setup_tasks, data)

        def test_coverage_diff(self):
            start_time = datetime(2012, 12, 12, tzinfo=get_current_timezone())
            b1 = Build.objects.create(project=self.project, branch='i', build_number=4,
                                      start_time=start_time)
            positive_change = BuildResult.objects.create(build=b1, coverage=100)
            self.assertEqual(positive_change.coverage_diff, 100)

            master = Build.objects.create(project=self.project, branch='master', build_number=3,
                                          end_time=start_time - timedelta(hours=1))
            BuildResult.objects.create(build=master, coverage=20)

            # Need to fetch again to come around cached_property
            self.assertEqual(BuildResult.objects.get(pk=positive_change.pk).coverage_diff, 80)

            b2 = Build.objects.create(project=self.project, branch='i', build_number=5,
                                      start_time=start_time)
            negative_change = BuildResult.objects.create(build=b2, coverage=10)
            self.assertEqual(negative_change.coverage_diff, -10)

            b3 = Build.objects.create(project=self.project, branch='i', build_number=6,
                                      start_time=start_time)
            no_change = BuildResult.objects.create(build=b3, coverage=20)
            self.assertEqual(no_change.coverage_diff, 0)
