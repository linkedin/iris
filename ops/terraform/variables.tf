variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "aws_key_name" {}
variable "aws_key_file" {}

variable "aws_region" {
  default = "us-west-2"
}

variable "vpc_cidr" {
  description = "CIDR for the whole VPC"
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR for the Public Subnet"
  default = "10.0.0.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR for the Private Subnet"
  default = "10.0.1.0/24"
}

variable "private_subnet_2b_cidr" {
  description = "CIDR for the Private Subnet"
  default = "10.0.2.0/24"
}

variable "private_subnet_2c_cidr" {
  description = "CIDR for the Private Subnet"
  default = "10.0.3.0/24"
}

variable "mysql_db_user" {
  default = "iris"
}

variable "mysql_db_pass" {
  default = "foobar123"
}

variable "mysql_db_database_name" {
  default = "iris"
}

variable "use_aws_rds_cluster" {
  default = false
}

variable "ssh_timeout" {
  default = "20s"
}
