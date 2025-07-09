variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "storm"
}

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be staging or production."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = ""
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.28"
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the cluster API - MUST be specified for security"
  type        = list(string)
  # No default - force users to explicitly specify allowed IPs
  validation {
    condition     = length(var.allowed_cidr_blocks) > 0
    error_message = "At least one CIDR block must be specified for cluster access. Never use 0.0.0.0/0 in production."
  }
}

# EKS Node Groups
variable "node_instance_types" {
  description = "Instance types for general node group"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge"]
}

variable "compute_instance_types" {
  description = "Instance types for compute node group"
  type        = list(string)
  default     = ["c5.2xlarge", "c5.4xlarge"]
}

variable "node_group_min_size" {
  description = "Minimum size of node group"
  type        = number
  default     = 3
}

variable "node_group_max_size" {
  description = "Maximum size of node group"
  type        = number
  default     = 10
}

variable "node_group_desired_size" {
  description = "Desired size of node group"
  type        = number
  default     = 3
}

# RDS
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

# Redis
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 2
}

# Monitoring
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# API Keys (sensitive) - MUST be provided via environment variables
variable "anthropic_api_key" {
  description = "Anthropic API key - provide via TF_VAR_anthropic_api_key environment variable"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.anthropic_api_key) > 0
    error_message = "Anthropic API key must be provided via TF_VAR_anthropic_api_key environment variable."
  }
}

variable "openai_api_key" {
  description = "OpenAI API key - provide via TF_VAR_openai_api_key environment variable"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.openai_api_key) > 0
    error_message = "OpenAI API key must be provided via TF_VAR_openai_api_key environment variable."
  }
}

variable "google_api_key" {
  description = "Google API key - provide via TF_VAR_google_api_key environment variable"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.google_api_key) > 0
    error_message = "Google API key must be provided via TF_VAR_google_api_key environment variable."
  }
}

variable "perplexity_api_key" {
  description = "Perplexity API key - provide via TF_VAR_perplexity_api_key environment variable"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.perplexity_api_key) > 0
    error_message = "Perplexity API key must be provided via TF_VAR_perplexity_api_key environment variable."
  }
}

# Domain
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
  default     = ""
}

# Tags
variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# Service Account Configuration
variable "app_k8s_namespace" {
  description = "Kubernetes namespace for the application"
  type        = string
  default     = "storm-production"
}

variable "app_k8s_service_account_name" {
  description = "Kubernetes service account name for the application"
  type        = string
  default     = "storm-app"
}

variable "project_owner" {
  description = "Project owner for tagging"
  type        = string
  default     = ""
}
