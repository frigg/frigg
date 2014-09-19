# coding=utf-8
import os
from fabric.decorators import task
from fabric.state import env
from django_fabric import App
import sys

sys.path.append(os.path.dirname(__file__))

env.user = 'ubuntu'
env.hosts = ['balder.tind.io']


class FriggApp(App):
    def pre_deploy_notify(self, instance):
        pass
        # code_dir = self.project_paths[instance]
        # with cd(code_dir):
        # self.run('cp frigg/settings/local_dummy.py frigg/settings/local.py')


site = FriggApp(
    project_paths={
        'prod': '/opt/frigg/',
    },
    urls={
        'prod': 'https://frigg.tind.io/github-webhook/'
    },
    restart_command={
        'prod': 'sudo supervisorctl restart frigg'
    },
    project_package='frigg',
    test_settings='frigg.settings.test',
)

deploy = task(site.deploy)
test = task(site.test)
clone_data = task(site.clone_data, "prod")