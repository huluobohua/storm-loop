# STORM Production Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Architecture](#architecture)
5. [Deployment Options](#deployment-options)
6. [Security Configuration](#security-configuration)
7. [Monitoring & Observability](#monitoring--observability)
8. [Scaling & Performance](#scaling--performance)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Overview

STORM (Synthesis of Topic Outline through Retrieval and Multi-perspective question asking) is a production-grade academic research platform designed for institutional deployment. This guide covers deployment strategies for various scales and requirements.

### Key Features
- **Multi-tenant architecture** supporting multiple institutions
- **Enterprise-grade security** with JWT auth, OAuth, and RBAC
- **Auto-scaling** capabilities for handling research workloads
- **Comprehensive monitoring** with Prometheus, Grafana, and ELK stack
- **High availability** with zero-downtime deployments

## Prerequisites

### Technical Requirements
- **Kubernetes**: 1.25+ (production) or Docker Compose (development)
- **PostgreSQL**: 15+ with extensions (uuid-ossp, pg_trgm)
- **Redis**: 7+ for caching and session management
- **Storage**: 100GB+ SSD for application data
- **SSL Certificates**: For HTTPS endpoints

### Required API Keys
At least one LLM provider:
- **Google Gemini API** (recommended)
- **OpenAI API**
- **Anthropic Claude API**

Optional search providers:
- **Perplexity API** (recommended for research)
- **Bing Search API**
- **Serper API**

### System Resources
**Minimum (Development)**:
- 4 CPU cores
- 8GB RAM
- 50GB storage

**Recommended (Production)**:
- 16+ CPU cores
- 32GB+ RAM
- 500GB+ SSD storage
- Load balancer
- CDN for static assets

## Quick Start

### 1. Local Development with Docker Compose

```bash
# Clone repository
git clone https://github.com/yourusername/storm-loop.git
cd storm-loop

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Start services
cd deployment/docker
docker-compose up -d

# Access application
# Web UI: http://localhost:8501
# API: http://localhost:8501/api/v1
```

### 2. Production Deployment with Kubernetes

```bash
# Create namespace
kubectl apply -f deployment/kubernetes/namespace.yaml

# Create secrets (edit with your values first)
kubectl create secret generic storm-secrets \
  --from-env-file=.env \
  -n storm-production

# Deploy infrastructure
kubectl apply -f deployment/kubernetes/postgres.yaml
kubectl apply -f deployment/kubernetes/redis.yaml
kubectl apply -f deployment/kubernetes/qdrant.yaml

# Deploy application
kubectl apply -f deployment/kubernetes/configmap.yaml
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/service.yaml
kubectl apply -f deployment/kubernetes/ingress.yaml

# Enable auto-scaling
kubectl apply -f deployment/kubernetes/hpa.yaml
```

## Architecture

### System Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Load Balancer │────▶│   Web Frontend  │────▶│   API Backend   │
│    (Nginx)      │     │   (Streamlit)   │     │    (FastAPI)    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                │                         │
                                ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │                 │     │                 │
                        │   Redis Cache   │     │   PostgreSQL    │
                        │                 │     │    Database     │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  Qdrant Vector  │
                                                │    Database     │
                                                │                 │
                                                └─────────────────┘
```

### Security Layers

1. **Network Security**
   - SSL/TLS termination at load balancer
   - Network policies for pod-to-pod communication
   - Private subnets for databases

2. **Application Security**
   - JWT authentication with refresh tokens
   - OAuth 2.0 for institutional SSO
   - Role-based access control (RBAC)
   - API rate limiting

3. **Data Security**
   - Encryption at rest for databases
   - Encrypted API keys and secrets
   - Audit logging for compliance

## Deployment Options

### 1. Kubernetes (Recommended for Production)

**Advantages**:
- Auto-scaling based on load
- Self-healing capabilities
- Rolling updates with zero downtime
- Multi-region deployment support

**Setup**:
See [kubernetes deployment guide](./KUBERNETES_DEPLOYMENT.md)

### 2. Docker Compose (Development/Small Scale)

**Advantages**:
- Simple setup
- Good for small teams (<100 users)
- Lower operational overhead

**Limitations**:
- Manual scaling
- No automatic failover
- Single point of failure

### 3. Managed Cloud Services

**AWS**:
- EKS for Kubernetes
- RDS for PostgreSQL
- ElastiCache for Redis
- Application Load Balancer

**Google Cloud**:
- GKE for Kubernetes
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud Load Balancing

**Azure**:
- AKS for Kubernetes
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Load Balancer

## Security Configuration

### 1. Environment Variables

Create a secure `.env` file:

```bash
# Core Configuration
STORM_ENV=production
JWT_SECRET=$(openssl rand -hex 32)
SESSION_SECRET=$(openssl rand -hex 32)

# Database
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# API Keys (encrypt in production)
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
GOOGLE_API_KEY=your-key-here
PERPLEXITY_API_KEY=your-key-here

# OAuth Configuration
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# Monitoring
GRAFANA_PASSWORD=$(openssl rand -base64 16)
```

### 2. SSL/TLS Configuration

```yaml
# cert-manager for automatic SSL
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### 3. RBAC Configuration

Default roles:
- **Guest**: Read-only access
- **User**: Create and manage own research
- **Researcher**: Advanced features + sharing
- **Institution Admin**: Manage institution users
- **System Admin**: Full system access

### 4. API Security

Rate limits by endpoint:
- `/api/v1/auth/*`: 5 requests/hour
- `/api/v1/research/generate`: 10 requests/hour
- `/api/v1/export`: 20 requests/hour
- Default: 100 requests/hour

## Monitoring & Observability

### 1. Metrics (Prometheus)

Key metrics to monitor:
- **Request rate & latency**
- **Research generation success rate**
- **API usage by institution**
- **Database connection pool**
- **Cache hit rates**

Access Prometheus:
```bash
kubectl port-forward -n storm-production svc/prometheus 9090:9090
```

### 2. Dashboards (Grafana)

Pre-built dashboards:
- **Application Overview**: Request rates, errors, latency
- **Research Analytics**: Generation rates, completion times
- **Infrastructure**: CPU, memory, disk usage
- **Business Metrics**: Users, institutions, usage

Access Grafana:
```bash
kubectl port-forward -n storm-production svc/grafana 3000:3000
# Default login: admin / <GRAFANA_PASSWORD>
```

### 3. Logging (ELK Stack)

Log aggregation setup:
- **Elasticsearch**: Log storage and search
- **Logstash/Filebeat**: Log collection
- **Kibana**: Log visualization

Important log queries:
```
# Failed research generations
level:error AND service:storm-app AND module:research

# Authentication failures
level:warn AND service:storm-app AND message:"authentication failed"

# Rate limit violations
level:warn AND service:storm-app AND message:"rate limit exceeded"
```

### 4. Alerts

Critical alerts configured:
- High error rate (>5%)
- Response time >5s (95th percentile)
- Database connection exhaustion
- Disk space <10%
- Pod restart loops

## Scaling & Performance

### 1. Horizontal Pod Autoscaling

```yaml
# Configured in hpa.yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: 80
```

### 2. Database Optimization

PostgreSQL tuning:
```sql
-- Connection pooling
max_connections = 200
shared_buffers = 8GB
effective_cache_size = 24GB

-- Query optimization
work_mem = 128MB
maintenance_work_mem = 2GB
```

### 3. Caching Strategy

Redis configuration:
- **Session cache**: 24h TTL
- **API response cache**: 1h TTL
- **Research results**: 7d TTL
- **LRU eviction policy**

### 4. Load Testing

Using k6 for load testing:
```javascript
// k6-load-test.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 100 },
    { duration: '10m', target: 100 },
    { duration: '5m', target: 0 },
  ],
};

export default function() {
  let response = http.get('https://storm.yourdomain.com/api/v1/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

## Backup & Recovery

### 1. Database Backups

Automated PostgreSQL backups:
```bash
# Create backup CronJob
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: storm-production
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h postgres-service -U storm storm > /backup/storm-\$(date +%Y%m%d).sql
              # Upload to S3
              aws s3 cp /backup/storm-\$(date +%Y%m%d).sql s3://storm-backups/
          restartPolicy: OnFailure
EOF
```

### 2. Disaster Recovery

Recovery Time Objective (RTO): 1 hour
Recovery Point Objective (RPO): 24 hours

Steps:
1. Deploy infrastructure from Terraform
2. Restore database from latest backup
3. Deploy application with latest image
4. Verify data integrity
5. Update DNS records

### 3. Data Export

User data export for GDPR compliance:
```bash
# Export user data
python manage.py export_user_data --user-id=<uuid> --format=json
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   kubectl top pods -n storm-production
   
   # Increase memory limits
   kubectl edit deployment storm-app -n storm-production
   ```

2. **Database Connection Errors**
   ```bash
   # Check connection pool
   kubectl exec -it postgres-0 -n storm-production -- psql -U storm -c "SELECT count(*) FROM pg_stat_activity;"
   
   # Increase pool size
   kubectl edit configmap storm-config -n storm-production
   ```

3. **Rate Limit Issues**
   ```bash
   # Check rate limit metrics
   kubectl logs -n storm-production -l app=storm --tail=100 | grep "rate limit"
   
   # Adjust limits
   kubectl edit configmap storm-config -n storm-production
   ```

### Debug Commands

```bash
# Get pod logs
kubectl logs -f <pod-name> -n storm-production

# Execute commands in pod
kubectl exec -it <pod-name> -n storm-production -- /bin/bash

# Describe pod issues
kubectl describe pod <pod-name> -n storm-production

# Check events
kubectl get events -n storm-production --sort-by='.lastTimestamp'
```

### Performance Profiling

```python
# Enable profiling
STORM_PROFILING=true

# Access profiling data
curl http://localhost:8501/debug/pprof/profile?seconds=30 > profile.pprof
go tool pprof -http=:8080 profile.pprof
```

## Support

For production support:
- **Documentation**: [https://docs.storm.ai](https://docs.storm.ai)
- **Community**: [https://community.storm.ai](https://community.storm.ai)
- **Enterprise Support**: support@storm.ai

---

Last Updated: January 2025
Version: 1.0.0