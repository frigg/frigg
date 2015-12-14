from django.contrib.auth import get_user_model
from django.db import models

from frigg import settings
from frigg.helpers import github


class Owner(models.Model):
    ORGANIZATION = 'organization'
    USER = 'user'
    TYPES = (
        ('Organization', ORGANIZATION),
        ('User', USER),
    )

    name = models.CharField(max_length=100)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='accounts')
    queue_name = models.CharField(max_length=200, default=settings.FRIGG_WORKER_QUEUE)
    image = models.CharField(max_length=200, default="", blank=True)
    account_type = models.CharField(max_length=40, choices=TYPES, null=True)

    def __str__(self):
        return self.name

    @property
    def github_token(self):
        try:
            token = self.members.first().github_token
        except AttributeError:
            token = None

        if not token:
            token = getattr(settings, 'GITHUB_ACCESS_TOKEN', ':')
        return token

    @property
    def number_of_members(self):
        return self.members.count()

    def update_members(self):
        collaborators = github.list_collaborators(self)
        users = get_user_model().objects.filter(username__in=collaborators)
        self.members = users
