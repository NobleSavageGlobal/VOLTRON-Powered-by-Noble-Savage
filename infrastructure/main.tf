terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "bba-command-os"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "database" {
  source = "./modules/database"

  db_name         = var.db_name
  db_username     = var.db_username
  db_password     = var.db_password
  instance_class  = var.db_instance_class
  environment     = var.environment
  subnet_ids      = var.subnet_ids
  security_groups = [aws_security_group.rds.id]
}

module "cache" {
  source = "./modules/cache"

  cluster_id      = "bba-redis-${var.environment}"
  node_type       = var.redis_node_type
  environment     = var.environment
  subnet_ids      = var.subnet_ids
  security_groups = [aws_security_group.redis.id]
}

module "storage" {
  source = "./modules/storage"

  bucket_name = var.s3_bucket_name
  environment = var.environment
}

module "app" {
  source = "./modules/app"

  app_name       = "bba-command-os"
  environment    = var.environment
  aws_region     = var.aws_region
  backend_image  = var.backend_image
  frontend_image = var.frontend_image
  backend_cpu    = var.backend_cpu
  backend_memory = var.backend_memory
  database_url   = module.database.connection_string
  redis_url      = module.cache.connection_string
  s3_bucket      = module.storage.bucket_name
  secret_key     = var.app_secret_key
  openai_api_key = var.openai_api_key
  subnet_ids     = var.subnet_ids
  security_groups = [aws_security_group.app.id]
}

resource "aws_security_group" "rds" {
  name        = "bba-rds-${var.environment}"
  description = "Allow PostgreSQL access from app"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}

resource "aws_security_group" "redis" {
  name        = "bba-redis-${var.environment}"
  description = "Allow Redis access from app"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}

resource "aws_security_group" "app" {
  name        = "bba-app-${var.environment}"
  description = "BBA Command OS application security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
