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

resource "aws_db_subnet_group" "iris_db" {
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



# RDS MySQL cluster

resource "aws_rds_cluster" "rds_iris" {
  depends_on = ["aws_db_subnet_group.iris_db"]
  count = "${var.use_aws_rds_cluster ? 1 : 0}"
  cluster_identifier = "aurora-cluster-iris"
  availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]
  database_name = "iris"
  master_username = "foo"
  master_password = "foobar123"
  backup_retention_period = 7
  preferred_backup_window = "07:00-09:00"
  vpc_security_group_ids = ["${aws_security_group.db.id}"]
  db_subnet_group_name = "${aws_db_subnet_group.iris_db.id}"
  final_snapshot_identifier = "iris-mysql"
  skip_final_snapshot = true
}

resource "aws_rds_cluster_instance" "rds_cluster_instances" {
  count = "${var.use_aws_rds_cluster ? 2 : 0}"
  identifier = "aurora-cluster-iris-${count.index}"
  cluster_identifier = "${aws_rds_cluster.rds_iris.id}"
  instance_class = "db.t2.small"
  publicly_accessible = false
}

output "rds_cluster_endpoint" {
  value = "${aws_rds_cluster.rds_iris.endpoint}"
}


# RDS MySQL instance

resource "aws_db_instance" "mysql_iris" {
  depends_on = ["aws_db_subnet_group.iris_db"]
  count = "${var.use_aws_rds_cluster ? 0 : 1}"
  allocated_storage    = 5
  storage_type         = "standard"
  engine               = "mysql"
  engine_version       = "5.7.16"
  instance_class       = "db.t2.micro"
  name                 = "iris"
  username             = "iris"
  password             = "foobar123"
  db_subnet_group_name = "${aws_db_subnet_group.iris_db.id}"
  final_snapshot_identifier = "iris-mysql"
  vpc_security_group_ids = ["${aws_security_group.db.id}"]
  skip_final_snapshot = true
}

output "rds_mysql_address" {
  value = "${aws_db_instance.mysql_iris.address}"
}
