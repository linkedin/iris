#FROM gitpod/workspace-full
FROM gitpod/workspace-base

RUN sudo apt-get update && sudo apt-get -y -o Dpkg::Options::=--force-confold dist-upgrade && \
    DEBIAN_FRONTEND=noninteractive sudo apt-get -y -o Dpkg::Options::=--force-confold install \
        libffi-dev libsasl2-dev python3-dev libyaml-dev \
        libldap2-dev libssl-dev python3-pip python3-setuptools python3-venv \
        mysql-client nginx uwsgi uwsgi-plugin-python3 uwsgi-plugin-gevent-python3 \
    && pip3 install mysql-connector-python \
    && sudo rm -rf /var/cache/apt/archives/*
