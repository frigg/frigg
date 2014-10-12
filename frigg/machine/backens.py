import os
import docker

from django.conf import settings

from fabric.operations import sudo
from fabric.state import env


class DockerBackend(object):
    def __init__(self, id, name):
        self.name = name
        self.id = id
        self.ssh_port = 15000 + self.id
        self.http_port = 18000 + self.id
        self.client = docker.Client(base_url=settings.DOCKER_SOCKET,
                                    timeout=10)

    def __build_dockerfile(self):
        self.client.build(path=os.path.join(settings.BASE_DIR, "templates"), tag="frigg_basic")

    def create(self):
        self.__build_dockerfile()

        self.client.create_container("frigg_basic", name=self.name)

    def start(self):
        self.client.start(self.name, port_bindings={80: ("0.0.0.0", self.http_port),
                                                    22: ("0.0.0.0", self.ssh_port)})

    def stop(self):
        self.client.stop(self.name)
        pass

    def run(self, cmd, capture=False):
        env.host_string = settings.DOCKER_IP + ":%s" % self.ssh_port
        env.user = "root"
        env.password = "screencast"

        return sudo(cmd, pty=True)

