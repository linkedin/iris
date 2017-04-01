Iris-API (and iris-sender) under Docker
======================================

**NOTE: Not mainatined anymore, please build latest docker image from provided packer setup.
See: ../packer/README.md**

### Get started

Build container. This installs all dependencies as well as copies all iris source code.

    docker build -t iris .

Edit iris's config file as needed (MySQL and vendor settings and so on):

    vim docker/config/config.yaml

Run it, with bind mounts to give access to iris api config file

    docker run -p 16649:16649 -v `pwd`/docker/config:/home/iris/config -t iris

You can optionally bind mount log directories for uwsgi/nginx:

    mkdir -p docker/logs/{uwsgi,nginx}
    docker run -p 16649:16649 -v `pwd`/docker/config:/home/iris/config \
    -v `pwd`/docker/logs/nginx:/home/iris/var/log/nginx  \
    -v `pwd`/docker/logs/uwsgi:/home/iris/var/log/uwsgi  -t iris

You can then hit `http://localhost:16649 ` to access iris running within the docker.

### Quick commands

Check what containers are running:

    docker ps

Kill and remove a container:

    docker rm -f $ID

Execute a bash shell inside container while it's running:

    docker exec -i -t $ID /bin/bash
