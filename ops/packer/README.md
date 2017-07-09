Build steps
-----------

Generate JSON for packer:

```bash
python gen_packer_cfg.py ./iris.yaml
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

Spin up an Iris instance and connect to existing MySQL DB:

```bash
docker run -d -e DOCKER_DB_BOOTSTRAP=1 \
	-e IRIS_CFG_DB_USER=root -e IRIS_CFG_DB_PASSWORD=admin -e IRIS_CFG_DB_HOST=IP_ADDRESS \
	--name iris -p 16649:16649 \
	quay.io/iris/iris:latest
```


Inspect docker image with docker run:

```bash
docker run --rm=true -i -t quay.io/iris/iris:latest /bin/bash
```
