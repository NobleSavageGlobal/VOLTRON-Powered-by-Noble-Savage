variable "app_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }
variable "backend_image" { type = string }
variable "frontend_image" { type = string }
variable "backend_cpu" { type = number; default = 512 }
variable "backend_memory" { type = number; default = 1024 }
variable "database_url" { type = string; sensitive = true }
variable "redis_url" { type = string }
variable "s3_bucket" { type = string }
variable "secret_key" { type = string; sensitive = true }
variable "openai_api_key" { type = string; sensitive = true; default = "" }
variable "subnet_ids" { type = list(string) }
variable "security_groups" { type = list(string) }

resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-${var.environment}"
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.app_name}-ecs-execution-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.app_name}-backend-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name  = "backend"
    image = var.backend_image
    portMappings = [{ containerPort = 8000 }]
    environment = [
      { name = "DATABASE_URL", value = var.database_url },
      { name = "REDIS_URL", value = var.redis_url },
      { name = "S3_BUCKET", value = var.s3_bucket },
      { name = "STORAGE_BACKEND", value = "s3" },
      { name = "ENVIRONMENT", value = var.environment },
    ]
    secrets = [
      { name = "SECRET_KEY", valueFrom = aws_ssm_parameter.secret_key.arn },
      { name = "OPENAI_API_KEY", valueFrom = aws_ssm_parameter.openai_key.arn },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = "/ecs/${var.app_name}-backend"
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
}

resource "aws_ssm_parameter" "secret_key" {
  name  = "/${var.app_name}/${var.environment}/secret_key"
  type  = "SecureString"
  value = var.secret_key
}

resource "aws_ssm_parameter" "openai_key" {
  name  = "/${var.app_name}/${var.environment}/openai_api_key"
  type  = "SecureString"
  value = var.openai_api_key != "" ? var.openai_api_key : "placeholder"
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.app_name}-backend"
  retention_in_days = 30
}

resource "aws_ecs_service" "backend" {
  name            = "${var.app_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_groups
    assign_public_ip = false
  }
}

output "backend_url" {
  value = "http://${aws_ecs_service.backend.name}.${var.environment}.local:8000"
}

output "frontend_url" {
  value = "http://${var.app_name}.${var.environment}.local:3000"
}
