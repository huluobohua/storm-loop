# STORM Production Deployment Infrastructure

This directory contains all necessary infrastructure code and configurations for deploying STORM to production environments.

## 📁 Directory Structure

```
deployment/
├── docker/                 # Docker configurations
│   ├── Dockerfile         # Main application container
│   ├── docker-compose.yml # Local development stack
│   └── docker-compose.prod.yml # Production stack
├── kubernetes/            # Kubernetes manifests
│   ├── namespace.yaml    # Namespace and resource quotas
│   ├── deployment.yaml   # Application deployments
│   ├── service.yaml      # Service definitions
│   ├── ingress.yaml      # Ingress rules
│   ├── hpa.yaml          # Horizontal Pod Autoscaler
│   └── *.yaml            # Other K8s resources
├── terraform/             # Infrastructure as Code
│   ├── main.tf           # Main Terraform configuration
│   ├── variables.tf      # Variable definitions
│   └── security.tf       # Security configurations
├── monitoring/            # Observability stack
│   ├── prometheus.yml    # Prometheus configuration
│   ├── alerts/           # Alert rules
│   └── grafana-dashboard.json # Grafana dashboards
├── docs/                  # Documentation
│   └── DEPLOYMENT_GUIDE.md # Comprehensive guide
└── scripts/               # Deployment scripts
```

## 🚀 Quick Start

### Local Development

```bash
cd deployment/docker
docker-compose up -d
```

### Production Deployment

1. **Infrastructure Setup (Terraform)**
   ```bash
   cd deployment/terraform
   terraform init
   terraform plan -var="environment=production"
   terraform apply -var="environment=production"
   ```

2. **Deploy to Kubernetes**
   ```bash
   cd deployment/kubernetes
   kubectl apply -f namespace.yaml
   kubectl apply -f .
   ```

## 🔒 Security Features

- **JWT Authentication** with refresh tokens
- **OAuth 2.0** integration for institutional SSO
- **Role-Based Access Control** (RBAC)
- **API Rate Limiting** per endpoint
- **WAF Protection** against common attacks
- **End-to-end encryption** for data in transit
- **Secrets management** with AWS Secrets Manager

## 📊 Monitoring & Observability

- **Prometheus** for metrics collection
- **Grafana** for visualization
- **ELK Stack** for log aggregation
- **Custom health checks** and probes
- **Distributed tracing** support

## 🔧 Configuration

### Required Environment Variables

```bash
# Core
STORM_ENV=production
JWT_SECRET=<generated>
POSTGRES_PASSWORD=<generated>
REDIS_PASSWORD=<generated>

# API Keys (at least one required)
ANTHROPIC_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
GOOGLE_API_KEY=<your-key>
PERPLEXITY_API_KEY=<your-key>

# OAuth (optional)
OAUTH_CLIENT_ID=<your-client-id>
OAUTH_CLIENT_SECRET=<your-secret>
```

## 📈 Scaling

The infrastructure supports:
- **Horizontal Pod Autoscaling** based on CPU/memory
- **Cluster Autoscaling** for node groups
- **Database read replicas** for scale-out
- **CDN integration** for static assets
- **Multi-region deployment** capability

## 🔄 CI/CD Pipeline

GitHub Actions workflow includes:
1. Security scanning (Trivy, Bandit)
2. Code quality checks (Ruff, Black)
3. Comprehensive test suite
4. Docker image building
5. Automated deployment (staging → production)
6. Post-deployment verification

## 🛡️ Disaster Recovery

- **RTO**: 1 hour
- **RPO**: 24 hours
- **Automated backups** for databases
- **Multi-AZ deployment** for high availability
- **Snapshot retention** for 30 days

## 📝 License

This deployment infrastructure is part of the STORM Academic Research Platform.

---

For detailed deployment instructions, see [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)