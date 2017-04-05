Iris sample terraform config for AWS
====================================

Overview
--------

This sample terraform spins up a cluster consists of the following services:

* 1 NAT server
* 1 app server (iris, iris-sender, nginx) in public subnset
* 1 RDS cluster in private subnet
* 2 elastic IPs


Usage
-----

Verify intended state:

```bash
terraform plan -var 'aws_access_key=AAAAAAAAAAAAAAAAAAAA' -var 'aws_secret_key=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
```

Deploy:

```bash
terraform apply -var 'aws_access_key=AAAAAAAAAAAAAAAAAAAA' -var 'aws_secret_key=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
```

Access to NAT server as bastion host:

```bash
# make sure your AWS ssh key is loaded through ssh-add
ssh -A -i YOUR_AWS_SSH_KEY ec2-user@NAT_SERVER
```

Access to Iris app node from NAT server:

```bash
ssh ubuntu@APP_SERVER_INTERNAL_IP
```
