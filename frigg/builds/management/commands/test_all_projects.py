# -*- coding: utf8 -*-

from django.core.management.base import BaseCommand
from frigg.builds.models import Build


class Command(BaseCommand):

    def handle(self, *args, **options):
        for project in Build.objects.all():
            project.run_tests()
