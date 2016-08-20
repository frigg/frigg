# -*- coding: utf8 -*-
import logging
from datetime import timedelta
from functools import lru_cache

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from frigg.builds.models import Build

logger = logging.getLogger(__name__)


@lru_cache()
def get_ids_of_five_last_builds_for_project(project_id):
    return [build.id for build in Build.objects.filter(project_id=project_id)[:5]]


class Command(BaseCommand):
    help = 'Delete logs for builds that are older than {0} hours.'.format(
        settings.FRIGG_KEEP_BUILD_LOGS_TIMEDELTA
    )

    def handle(self, *args, **options):
        delta = timedelta(hours=settings.FRIGG_KEEP_BUILD_LOGS_TIMEDELTA)

        for build in Build.objects.filter(end_time__lt=now() - delta):
            five_last_builds = get_ids_of_five_last_builds_for_project(build.project.pk)
            if build.pk in five_last_builds:
                continue

            try:
                build.delete_logs()
            except Exception as error:
                logger.exception(error)
