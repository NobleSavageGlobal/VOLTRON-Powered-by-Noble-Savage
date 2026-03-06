variable "db_name" { type = string }
variable "db_username" { type = string }
variable "db_password" { type = string; sensitive = true }
variable "instance_class" { type = string; default = "db.t3.micro" }
variable "environment" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_groups" { type = list(string) }

resource "aws_db_subnet_group" "main" {
  name       = "bba-db-subnet-${var.environment}"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "main" {
  identifier        = "bba-postgres-${var.environment}"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = var.instance_class
  db_name           = var.db_name
  username          = var.db_username
  password          = var.db_password
  storage_encrypted = true
  deletion_protection = var.environment == "production"
  skip_final_snapshot = var.environment != "production"

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_groups

  backup_retention_period = var.environment == "production" ? 7 : 1
}

output "endpoint" {
  value = aws_db_instance.main.address
}

output "connection_string" {
  value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:5432/${var.db_name}"
  sensitive = true
}
