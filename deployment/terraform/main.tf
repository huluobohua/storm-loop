# Terraform backend configuration moved to providers.tf
# to avoid duplicate terraform blocks

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Module
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"
  
  name = "${var.project_name}-${var.environment}-vpc"
  cidr = var.vpc_cidr
  
  azs             = data.aws_availability_zones.available.names
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  database_subnets = var.database_subnet_cidrs
  
  enable_nat_gateway = true
  single_nat_gateway = var.environment == "staging"
  enable_dns_hostnames = true
  enable_dns_support = true
  
  enable_flow_log = true
  flow_log_destination_type = "cloud-watch-logs"
  
  tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
  
  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb" = "1"
  }
  
  private_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "19.17.2"
  
  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  enable_irsa = true
  
  cluster_endpoint_public_access  = false
  cluster_endpoint_private_access = true
  # Private-only access for maximum security
  
  cluster_addons = {
    coredns = {
      resolve_conflicts = "OVERWRITE"
    }
    kube-proxy = {}
    vpc-cni = {
      resolve_conflicts = "OVERWRITE"
    }
    aws-ebs-csi-driver = {
      resolve_conflicts = "OVERWRITE"
    }
  }
  
  eks_managed_node_groups = {
    general = {
      name = "${var.project_name}-general"
      
      instance_types = var.node_instance_types
      
      min_size     = var.node_group_min_size
      max_size     = var.node_group_max_size
      desired_size = var.node_group_desired_size
      
      disk_size = 100
      disk_type = "gp3"
      
      labels = {
        Environment = var.environment
        NodeGroup   = "general"
      }
      
      taints = []
    }
    
    compute = {
      name = "${var.project_name}-compute"
      
      instance_types = var.compute_instance_types
      
      min_size     = 0
      max_size     = 10
      desired_size = 2
      
      disk_size = 200
      disk_type = "gp3"
      
      labels = {
        Environment = var.environment
        NodeGroup   = "compute"
        Workload    = "research"
      }
      
      taints = [
        {
          key    = "workload"
          value  = "research"
          effect = "NO_SCHEDULE"
        }
      ]
    }
  }
  
  manage_aws_auth_configmap = true
  
  aws_auth_roles = [
    {
      rolearn  = aws_iam_role.eks_admin.arn
      username = "admin:{{SessionName}}"
      groups   = ["system:masters"]
    }
  ]
}

# RDS PostgreSQL
module "rds" {
  source = "terraform-aws-modules/rds/aws"
  version = "6.3.0"
  
  identifier = "${var.project_name}-${var.environment}-postgres"
  
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  storage_encrypted = true
  
  db_name  = "storm"
  username = "storm"
  manage_master_user_password = true
  master_user_secret_kms_key_id = aws_kms_key.main.key_id
  port     = "5432"
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  maintenance_window = "sun:02:00-sun:03:00"
  backup_window      = "03:00-06:00"
  backup_retention_period = 30
  
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  create_db_subnet_group = true
  subnet_ids = module.vpc.database_subnets
  
  family = "postgres15"
  major_engine_version = "15"
  
  deletion_protection = var.environment == "production"
  
  parameters = [
    {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements"
    },
    {
      name  = "log_min_duration_statement"
      value = "1000"  # Log queries taking more than 1 second
    }
  ]
}

# ElastiCache Redis
module "redis" {
  source = "terraform-aws-modules/elasticache/aws"
  version = "1.0.0"
  
  cluster_id = "${var.project_name}-${var.environment}-redis"
  
  engine          = "redis"
  engine_version  = "7.0"
  node_type       = var.redis_node_type
  num_cache_nodes = var.redis_num_nodes
  
  subnet_ids = module.vpc.private_subnets
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token_enabled = true
  auth_token = random_password.redis_password.result
  
  automatic_failover_enabled = var.redis_num_nodes > 1
  
  snapshot_retention_limit = 5
  snapshot_window = "03:00-05:00"
}

# S3 Buckets
resource "aws_s3_bucket" "storage" {
  bucket = "${var.project_name}-${var.environment}-storage"
}

resource "aws_s3_bucket_versioning" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "storage" {
  bucket = aws_s3_bucket.storage.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  
  enable_deletion_protection = var.environment == "production"
  enable_http2 = true
}

# WAF
resource "aws_wafv2_web_acl" "main" {
  name  = "${var.project_name}-${var.environment}-waf"
  scope = "REGIONAL"
  
  default_action {
    allow {}
  }
  
  rule {
    name     = "RateLimitRule"
    priority = 1
    
    action {
      block {}
    }
    
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }
  
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2
    
    override_action {
      none {}
    }
    
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name               = "CommonRuleSet"
      sampled_requests_enabled   = true
    }
  }
  
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name               = "WAF"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "main" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/eks/${var.cluster_name}/app"
  retention_in_days = var.log_retention_days
}

# Secrets Manager
resource "aws_secretsmanager_secret" "api_keys" {
  name = "${var.project_name}-${var.environment}-api-keys"
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  
  secret_string = jsonencode({
    ANTHROPIC_API_KEY = var.anthropic_api_key
    OPENAI_API_KEY    = var.openai_api_key
    GOOGLE_API_KEY    = var.google_api_key
    PERPLEXITY_API_KEY = var.perplexity_api_key
  })
}

# Redis auth token secret
resource "aws_secretsmanager_secret" "redis_auth" {
  name = "${var.project_name}-${var.environment}-redis-auth"
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  secret_id     = aws_secretsmanager_secret.redis_auth.id
  secret_string = random_password.redis_password.result
}
