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
