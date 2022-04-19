FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get -y dist-upgrade \
    && apt-get -y install libffi-dev libsasl2-dev python3-dev libyaml-dev sudo \
        libldap2-dev libssl-dev python3-pip python3-setuptools python3-venv \
    mysql-client nginx uwsgi uwsgi-plugin-python3 uwsgi-plugin-gevent-python3 \
    && pip3 install mysql-connector-python \
    && rm -rf /var/cache/apt/archives/*

RUN useradd -m -s /bin/bash iris

COPY src /home/iris/source/src
COPY setup.py /home/iris/source/setup.py
COPY MANIFEST.in /home/iris/source/MANIFEST.in
COPY README.md /home/iris/source/README.md

WORKDIR /home/iris

RUN chown -R iris:iris /home/iris/source /var/log/nginx /var/lib/nginx \
    && sudo -Hu iris mkdir -p /home/iris/var/log/uwsgi /home/iris/var/log/nginx /home/iris/var/run /home/iris/var/relay \
    && sudo -Hu iris python3 -m venv /home/iris/env \
    && sudo -Hu iris /bin/bash -c 'source /home/iris/env/bin/activate && python3 -m pip install -U pip wheel && cd /home/iris/source && pip install .'

COPY ops/config/systemd /etc/systemd/system
COPY ops/daemons /home/iris/daemons
COPY ops/daemons/uwsgi-docker.yaml /home/iris/daemons/uwsgi.yaml
COPY db /home/iris/db
COPY configs /home/iris/config
COPY healthcheck /tmp/status
COPY ops/entrypoint.py /home/iris/entrypoint.py

RUN chown -R iris:iris /home/iris/

EXPOSE 16649

CMD ["sudo", "-EHu", "iris", "bash", "-c", "source /home/iris/env/bin/activate && python -u /home/iris/entrypoint.py"]
