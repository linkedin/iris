#FROM gitpod/workspace-full
FROM gitpod/workspace-base


# Install custom tools, runtime, etc.
#RUN brew install fzf

# ##RUN sudo apt-get update && \
#     DEBIAN_FRONTEND=noninteractive sudo apt-get -y -o Dpkg::Options::=--force-confold dist-upgrade && \
#     sudo apt-get install gnupg2 && \
#     wget https://repo.percona.com/apt/percona-release_latest.$(lsb_release -sc)_all.deb && \
#     sudo dpkg -i percona-release_latest.$(lsb_release -sc)_all.deb && \
#     rm percona-release_latest.$(lsb_release -sc)_all.deb && \
#     sudo apt-get update && \
#     DEBIAN_FRONTEND=noninteractive sudo -E apt-get -y -o Dpkg::Options::=--force-confold install percona-server-server-5.7 && \
#     sudo rm -rf /var/lib/apt/lists/*

RUN sudo apt-get update && sudo apt-get -y -o Dpkg::Options::=--force-confold dist-upgrade && \
    DEBIAN_FRONTEND=noninteractive sudo apt-get -y -o Dpkg::Options::=--force-confold install \
        libffi-dev libsasl2-dev python3-dev libyaml-dev \
        libldap2-dev libssl-dev python3-pip python3-setuptools python3-venv \
        mysql-client nginx uwsgi uwsgi-plugin-python3 uwsgi-plugin-gevent-python3 \
    && pip3 install mysql-connector-python \
    && sudo rm -rf /var/cache/apt/archives/*

#    && sudo -Hu iris python3 -m venv /home/iris/env \
#    && sudo -Hu iris /bin/bash -c 'source /home/iris/env/bin/activate && python3 -m pip install -U pip wheel && cd /home/iris/source && pip install .'

