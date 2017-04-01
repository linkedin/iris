FROM ubuntu:16.04

RUN apt-get update && apt-get -y dist-upgrade \
    && apt-get -y install python-pip uwsgi virtualenv sudo python-dev libyaml-dev \
       libsasl2-dev libldap2-dev nginx uwsgi-plugin-python mysql-client \
    && rm -rf /var/cache/apt/archives/*

RUN useradd -m -s /bin/bash iris

COPY ../../setup.py /home/iris/setup.py
COPY ../entrypoint.py /home/iris/entrypoint.py
ADD ../daemons /home/iris/daemons
ADD ../../db /home/iris/db
ADD ../../src /home/iris/source/src

RUN chown -R iris:iris /home/iris /var/log/nginx /var/lib/nginx \
    && sudo -Hu iris mkdir -p /home/iris/var/log/uwsgi /home/iris/var/log/nginx /home/iris/var/run \
    && sudo -Hu iris virtualenv /home/iris/env \
    && sudo -Hu iris /bin/bash -c 'source /home/iris/env/bin/activate && cd /home/iris && python setup.py install'

EXPOSE 16649

CMD ["sudo", "-Hu", "iris", "bash", "-c", "source /home/iris/env/bin/activate && python /home/iris/entrypoint.py"]
