variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (development/staging/production)"
  type        = string
  default     = "production"
}

variable "vpc_id" {
  description = "VPC ID for resources"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "bba_db"
}

variable "db_username" {
  description = "PostgreSQL username"
  type        = string
  default     = "bba"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for document storage"
  type        = string
  default     = "bba-command-os"
}

variable "backend_image" {
  description = "Docker image for backend"
  type        = string
}

variable "frontend_image" {
  description = "Docker image for frontend"
  type        = string
}

variable "backend_cpu" {
  description = "CPU units for backend task"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Memory MB for backend task"
  type        = number
  default     = 1024
}

variable "app_secret_key" {
  description = "Application secret key for JWT"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}
