resource "aws_security_group" "allow_ssh" {
  name = "vpc_allow_ssh"
  description = "Allow ssh connections."

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["${var.public_subnet_cidr}"]
  }

  vpc_id = "${aws_vpc.default.id}"

  tags {
    Name = "AllosSSHSG"
  }
}
