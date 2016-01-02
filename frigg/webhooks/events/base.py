import logging

from basis.compat import get_user_model

from frigg.builds.models import Build, BuildResult, Project
from frigg.owners.models import Owner

logger = logging.getLogger(__name__)


class Event(object):
    REPOSITORY_URL = '{event.repository_owner}/{event.repository_name}'
    ALLOWED_EVENT_TYPES = []

    def __init__(self, event_type, data):
        self.event_type = event_type
        self.data = data
        self.build = None
        self.project = None

    @property
    def repository_url(self):
        if self.repository_owner and self.repository_name:
            return self.REPOSITORY_URL.format(event=self)

    @property
    def message(self):
        return ''

    @property
    def should_build(self):
        if self.event_type == 'delete':
            return False
        if self.event_type == 'ping':
            return False
        if self.event_type == 'push':
            return '[ci skip]' not in self.message
        return not self.is_unknown_event_type

    @property
    def is_unknown_event_type(self):
        return self.event_type is None or self.event_type not in self.ALLOWED_EVENT_TYPES

    @property
    def response(self):
        if self.is_unknown_event_type and not self.event_type == 'ping':
            return 'Unknown event type "{event.event_type}"'.format(event=self)
        if self.build:
            return 'Handled "{event}" event.\nMore info at {url}'.format(
                event=self.event_type,
                url=self.build.get_absolute_url()
            )
        else:
            return 'Handled "{event}"'.format(event=self.event_type)

    @property
    def repository_owner(self):
        raise NotImplementedError

    @property
    def repository_name(self):
        raise NotImplementedError

    @property
    def repository_private(self):
        raise NotImplementedError

    @property
    def branch(self):
        raise NotImplementedError

    @property
    def hash(self):
        raise NotImplementedError

    @property
    def pull_request_id(self):
        raise NotImplementedError

    @property
    def author(self):
        raise NotImplementedError

    @property
    def is_retest_comment_event(self):
        raise NotImplementedError

    def handle(self):
        if self.is_unknown_event_type:
            return

        self.project = self.create_project()
        self.update_users()

        if self.should_build:
            self.start_build()
        else:
            if self.event_type == 'delete':

                for build in Build.objects.filter(end_time=None,
                                                  branch=self.branch,
                                                  project=self.project):

                    if build.is_pending:
                        BuildResult.objects.create(
                            build=build,
                            succeeded=False,
                            result_log=[{'task': '', 'error': 'Branch deleted before built'}]
                        )

    def update_users(self):
        try:
            user = get_user_model().objects.get(username=self.project.owner)

            # Must add a user before checking for more
            self.project.members.add(user)
            self.project.update_members()
        except get_user_model().DoesNotExist:
            logger.debug('Could not load users for new project '
                         '{event.repository_owner}/{event.repository_name}.'.format(event=self))

    def create_project(self):
        owner = Owner.objects.get_or_create(name=self.repository_owner)[0]
        project, created = Project.objects.get_or_create(
            owner=self.repository_owner,
            name=self.repository_name
        )

        if created:
            project.image = owner.image
            project.queue_name = owner.queue_name

        project.private = self.repository_private
        project.save()
        return project

    def start_build(self):
        if self.is_retest_comment_event:
            earlier_build = Build.objects.filter(
                project__owner=self.repository_owner,
                project__name=self.repository_name,
                pull_request_id=self.pull_request_id
            ).last()

            if earlier_build:
                self.project.start_build({
                    'branch': earlier_build.branch,
                    'sha': earlier_build.sha,
                    'author': earlier_build.author,
                    'pull_request_id': earlier_build.pull_request_id,
                    'message': earlier_build.message
                })
            else:
                logger.info('Retest comment event without earlier build')

        else:
            self.project.start_build({
                'branch': self.branch,
                'sha': self.hash,
                'author': self.author,
                'pull_request_id': self.pull_request_id,
                'message': self.message
            })
