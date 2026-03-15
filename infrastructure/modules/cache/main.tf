variable "cluster_id" { type = string }
variable "node_type" { type = string; default = "cache.t3.micro" }
variable "environment" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_groups" { type = list(string) }

resource "aws_elasticache_subnet_group" "main" {
  name       = "bba-redis-subnet-${var.environment}"
  subnet_ids = var.subnet_ids
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = var.cluster_id
  engine               = "redis"
  node_type            = var.node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = var.security_groups
}

output "endpoint" {
  value = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "connection_string" {
  value = "redis://${aws_elasticache_cluster.main.cache_nodes[0].address}:6379/0"
}
