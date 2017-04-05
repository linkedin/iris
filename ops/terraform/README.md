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

Set the following variables in `terraform.tfvars` file:

```
aws_access_key = "AAAAAAAAAAAAAAAAAAAA"
aws_secret_key = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
aws_key_name  = "aws-ssh"
aws_key_file = "/Users/foo/.ssh/aws-ssh.pem"
```

Verify intended state:

```bash
terraform plan
```

Deploy:

```bash
terraform apply
```

Find out public DNS via terraform output, look for key `iris_public_dns`:

```bash
terraform output
```

Iris can be accessed at `${iris_public_dns}:16649`.

Access to NAT server as bastion host:

```bash
# make sure your AWS ssh key is loaded through ssh-add
ssh -A -i YOUR_AWS_SSH_KEY ec2-user@NAT_SERVER
```

Access to Iris app node from NAT server:

```bash
ssh ubuntu@APP_SERVER_INTERNAL_IP
```
