from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Owner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False,
                                        auto_created=True)),
                ('name', models.CharField(max_length=100)),
                ('queue_name', models.CharField(max_length=200, default='frigg:queue')),
                ('image', models.CharField(max_length=200, default='', blank=True)),
                ('account_type', models.CharField(choices=[('organization', 'Organization'),
                                                           ('user', 'User')],
                                                  max_length=40, null=True)),
                ('members', models.ManyToManyField(to=settings.AUTH_USER_MODEL,
                                                   related_name='accounts', blank=True)),
            ],
        ),
    ]
