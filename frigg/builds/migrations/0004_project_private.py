# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('builds', '0003_project_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='private',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
