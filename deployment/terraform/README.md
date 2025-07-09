# STORM Infrastructure - Terraform Configuration

This directory contains Terraform configurations for provisioning the STORM application infrastructure on AWS.

## Architecture Overview

The infrastructure includes:
- **EKS Cluster**: Managed Kubernetes for container orchestration
- **RDS PostgreSQL**: Managed database with Multi-AZ deployment
- **ElastiCache Redis**: In-memory caching layer
- **S3 Buckets**: Object storage for application data
- **CloudFront CDN**: Content delivery network
- **Application Load Balancer**: Traffic distribution
- **WAF**: Web Application Firewall for security
- **VPC**: Isolated network with public/private subnets

## Prerequisites

1. **Terraform**: Version 1.3.0 or higher
2. **AWS CLI**: Configured with appropriate credentials
3. **kubectl**: For EKS cluster access
4. **helm**: For deploying Kubernetes applications

## Quick Start

1. **Configure Backend** (for state management):
   ```bash
   cp backend.hcl.example backend.hcl
   # Edit backend.hcl with your S3 bucket details
   ```

2. **Configure Variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your configuration
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init -backend-config=backend.hcl
   ```

4. **Plan Infrastructure**:
   ```bash
   terraform plan
   ```

5. **Apply Infrastructure**:
   ```bash
   terraform apply
   ```

## File Structure

- `providers.tf` - Provider configurations (AWS, Kubernetes, Helm)
- `main.tf` - Core infrastructure resources
- `security.tf` - Security-related resources (WAF, KMS, IAM)
- `variables.tf` - Input variable definitions
- `outputs.tf` - Output values for use by other systems
- `terraform.tfvars.example` - Example variable values
- `backend.hcl.example` - Example backend configuration

## Important Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region for resources | `us-west-2` |
| `environment` | Environment name (production/staging) | `production` |
| `vpc_cidr` | CIDR block for VPC | `10.0.0.0/16` |
| `eks_cluster_version` | Kubernetes version for EKS | `1.28` |
| `rds_instance_class` | RDS instance type | `db.r6g.large` |

## Outputs

Key outputs available after infrastructure creation:
- `eks_cluster_endpoint` - EKS cluster API endpoint
- `rds_endpoint` - RDS database endpoint
- `redis_endpoint` - ElastiCache Redis endpoint
- `alb_dns_name` - Load balancer DNS name
- `ecr_repository_url` - Docker registry URL

## Security Considerations

1. **State File**: Contains sensitive information - ensure S3 bucket is encrypted
2. **Secrets**: Use AWS Secrets Manager for sensitive values
3. **IAM**: Follow principle of least privilege
4. **Network**: Private subnets for databases and internal services
5. **Encryption**: All data at rest and in transit is encrypted

## Cost Optimization

To reduce costs in non-production environments:
1. Adjust instance sizes in `terraform.tfvars`
2. Reduce number of availability zones
3. Disable Multi-AZ for RDS
4. Use spot instances for EKS nodes

## Maintenance

1. **State Locking**: DynamoDB table prevents concurrent modifications
2. **Backups**: Automated backups for RDS and EBS volumes
3. **Monitoring**: CloudWatch dashboards and alarms included
4. **Updates**: Regularly update provider versions

## Troubleshooting

Common issues and solutions:

1. **State Lock Error**: Check DynamoDB table for stuck locks
2. **Permission Denied**: Ensure AWS credentials have necessary IAM permissions
3. **Resource Limits**: Request AWS service quota increases if needed

## Next Steps

After infrastructure is provisioned:
1. Deploy applications using Kubernetes manifests
2. Configure DNS records in Route53
3. Set up monitoring dashboards
4. Configure backup policies
5. Test disaster recovery procedures

For questions or issues, please refer to the main project documentation.