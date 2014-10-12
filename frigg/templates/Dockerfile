# sshd
#
# VERSION               0.0.1

FROM ubuntu:14.04
MAINTAINER FRIGG "thatcher@dotcloud.com"

#Packages
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y openssh-server python-setuptools python-dev python-distribute python-pip git
RUN pip install tox
RUN pip install flake8

RUN mkdir /opt/builds
RUN mkdir /var/run/sshd
RUN echo 'root:screencast' | chpasswd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

EXPOSE 22 80
CMD ["/usr/sbin/sshd", "-D"]
