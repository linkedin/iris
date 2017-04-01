resource "aws_security_group" "web" {
  name = "vpc_web"
  description = "Allow incoming HTTP connections."

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
    cidr_blocks = ["${var.private_subnet_cidr}"]
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
    mysql_db_host = "${aws_rds_cluster.rds_iris.endpoint}"
    mysql_db_user = "${var.mysql_db_user}"
    mysql_db_pass = "${var.mysql_db_pass}"
    mysql_db_database_name = "${var.mysql_db_database_name}"
  }
}

resource "aws_instance" "iris-1" {
  ami           = "ami-54881f34"
  availability_zone = "us-west-2a"
  instance_type = "t2.micro"
  key_name      = "${var.aws_key_name}"
  vpc_security_group_ids = [
    "${aws_security_group.web.id}",
    "${aws_security_group.allow_ssh.id}"
  ]
  subnet_id = "${aws_subnet.us-west-2a-public.id}"
  associate_public_ip_address = true
  source_dest_check = false

  provisioner "file" {
    content = "../config/systemd/uwsgi-iris.socket"
    destination = "/etc/systemd/system/uwsgi-iris.socket"
  }

  provisioner "file" {
    content = "../config/systemd/uwsgi-iris.service"
    destination = "/etc/systemd/system/uwsgi-iris.service"
  }

  provisioner "local-exec" {
    command = "echo \"${data.template_file.iris-config.rendered}\" > /home/iris/config/config.yaml"
  }

  tags {
    Name = "Iris node"
  }
}

resource "aws_eip" "iris-1-ip" {
  instance = "${aws_instance.iris-1.id}"
  vpc = true
}

output "iris_private_dns" {
  value = "${aws_instance.iris-1.private_dns}"
}

output "iris_public_dns" {
  value = "${aws_instance.iris-1.public_dns}"
}
