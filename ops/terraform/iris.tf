resource "aws_security_group" "web" {
  name = "vpc_web"
  description = "Allow incoming HTTP connections."

  /* TODO: migrate to 80 when nginx is controlled by systemd
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  */
  ingress {
    from_port = 16649
    to_port = 16649
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = -1
    to_port = -1
    protocol = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["${var.vpc_cidr}"]
  }

  egress { # MySQL
    from_port = 3306
    to_port = 3306
    protocol = "tcp"
    cidr_blocks = ["${var.vpc_cidr}"]
  }

  vpc_id = "${aws_vpc.default.id}"

  tags {
    Name = "WebServerSG"
  }
}


# Iris APP

data "template_file" "iris-config" {
  template = "${file("../config/iris/config.yaml.tpl")}"
  vars {
    /* mysql_db_host = "${var.use_aws_rds_cluster ? aws_rds_cluster.rds_iris.endpoint : aws_db_instance.mysql_iris.address}" */
    mysql_db_host = "${aws_db_instance.mysql_iris.address}"
    mysql_db_user = "${var.mysql_db_user}"
    mysql_db_pass = "${var.mysql_db_pass}"
    mysql_db_database_name = "${var.mysql_db_database_name}"
  }
}

data "aws_ami" "iris" {
  most_recent = true

  filter {
    name = "owner-id"
    values = ["797612478720"]
  }

  filter {
    name = "tag:type"
    values = ["packer_build"]
  }

  filter {
    name = "tag:app"
    values = ["iris"]
  }
}

resource "aws_instance" "iris-1" {
  ami = "${data.aws_ami.iris.id}"
  availability_zone = "us-west-2a"
  instance_type = "t2.micro"
  key_name = "${var.aws_key_name}"
  vpc_security_group_ids = [
    "${aws_security_group.web.id}",
    "${aws_security_group.allow_ssh.id}"
  ]
  subnet_id = "${aws_subnet.us-west-2a-public.id}"
  associate_public_ip_address = true
  source_dest_check = false

  connection {
    timeout = "${var.ssh_timeout}"
    type = "ssh"
    user = "ubuntu"
    host = "${aws_instance.iris-1.private_ip}"
    agent = true
    bastion_host = "${aws_instance.nat.public_dns}"
    bastion_user = "ec2-user"
    bastion_private_key = "${file(var.aws_key_file)}"
  }

  provisioner "file" {
    content = "${data.template_file.iris-config.rendered}"
    destination = "/home/ubuntu/iris-config.yaml"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo mv /home/ubuntu/iris-config.yaml /home/iris/config/config.yaml",
      "sudo systemctl start uwsgi-iris",
      "sudo systemctl start nginx-iris",
      "sleep 10 && curl localhost:16649/v0/applications && sudo -u iris bash -c 'echo GOOD > /home/iris/var/healthcheck_control'"
    ]
  }

  tags {
    Name = "Iris node"
  }
}

resource "aws_eip" "iris-1-ip" {
  instance = "${aws_instance.iris-1.id}"
  vpc = true
}

output "iris_private_ip" {
  value = "${aws_instance.iris-1.private_ip}"
}

output "iris_public_dns" {
  value = "${aws_instance.iris-1.public_dns}"
}
