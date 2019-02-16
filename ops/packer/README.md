Build steps
-----------

Generate JSON for packer:

```bash
mkdir output
python gen_packer_cfg.py ./iris.yaml | tail -n +2 > ./output/iris.json
```

Build and publish AWS AMI:

```bash
packer build -only=amazon-ebs \
    -var "aws_ssh_keypair_name=YOUR_KEY_NAME_IN_AWS" \
    -var "aws_ssh_private_key_file=$HOME/.ssh/AWS_KEY.pem" \
    -var "aws_access_key=AAAAAAAAAAAAAAAAAAAA" \
    -var "aws_secret_key=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB" \
    ./output/iris.json
```

Build Docker image:

```bash
packer build -only=docker ./output/iris.json
```


Usage
-----

### Docker

Set up mysql DB (if needed). 5.6 will work out-of-box. 5.7 requires a change to `SQL_MODE` to
remove `ONLY_FULL_GROUP_BY` (set `TRUE` as default for 5.7+). Find the IP address of the docker
container using docker inspect.
```bash
docker run --name iris_mysql -d -e MYSQL_ROOT_PASSWORD=admin mysql:5.6
export DB_IP_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' iris_mysql)
```

Spin up an Iris instance and connect to existing MySQL DB. Make sure user and password are
configure to match your MySQL setup (here, root:admin). These credentials should be changed
for non-toy deployments. If you're not using the container spun up in the previous paragraph,
replace `$DB_IP_ADDRESS` with the IP of your database host.

```bash
docker run -d -e DOCKER_DB_BOOTSTRAP=1 \
	-e IRIS_CFG_DB_USER=root -e IRIS_CFG_DB_PASSWORD=admin -e IRIS_CFG_DB_HOST=$DB_IP_ADDRESS \
	--name iris -p 16649:16649 \
	quay.io/iris/iris:latest
```


Inspect docker image with docker run:

```bash
docker run --rm=true -i -t quay.io/iris/iris:latest /bin/bash
```
