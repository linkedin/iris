resource "aws_security_group" "db" {
  name = "vpc_db"
  description = "Allow incoming database connections."

  ingress {
    from_port = 3306
    to_port = 3306
    protocol = "tcp"
    cidr_blocks = ["${var.vpc_cidr}"]
  }
  ingress {
    from_port = -1
    to_port = -1
    protocol = "icmp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  vpc_id = "${aws_vpc.default.id}"

  tags {
    Name = "DBServerSG"
  }
}

resource "aws_db_subnet_group" "db" {
    name = "main"
    description = "Our main group of DB subnets"
    subnet_ids = [
      "${aws_subnet.us-west-2a-private.id}",
      "${aws_subnet.us-west-2b-private.id}",
      "${aws_subnet.us-west-2c-private.id}"
    ]
    tags {
      Name = "Iris MySQL DB subnet group"
    }
}


# DB

resource "aws_rds_cluster" "rds_iris" {
  cluster_identifier = "aurora-cluster-iris"
  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
  database_name = "iris"
  master_username = "foo"
  master_password = "foobar123"
  backup_retention_period = 7
  preferred_backup_window = "07:00-09:00"
  vpc_security_group_ids = ["${aws_security_group.db.id}"]
  db_subnet_group_name = "${aws_db_subnet_group.db.id}"
}

resource "aws_rds_cluster_instance" "rds_cluster_instances" {
  count = 2
  identifier = "aurora-cluster-iris-${count.index}"
  cluster_identifier = "${aws_rds_cluster.rds_iris.id}"
  instance_class = "db.t2.small"
  publicly_accessible = false
}

output "rds_cluster_endpoint" {
  value = "${aws_rds_cluster.rds_iris.endpoint}"
}
