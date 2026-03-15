output "database_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.database.endpoint
}

output "cache_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.cache.endpoint
}

output "storage_bucket" {
  description = "S3 bucket name"
  value       = module.storage.bucket_name
}

output "backend_service_url" {
  description = "Backend ECS service URL"
  value       = module.app.backend_url
}

output "frontend_service_url" {
  description = "Frontend ECS service URL"
  value       = module.app.frontend_url
}
