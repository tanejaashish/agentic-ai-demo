# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Agentic AI Demo system.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Sufficient cluster resources:
  - At least 3 nodes (recommended)
  - 16GB+ total RAM
  - 8+ CPU cores

## Quick Deployment

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Create Persistent Volume Claims

```bash
kubectl apply -f pvcs.yaml
```

### 3. Deploy Services

```bash
# Deploy Redis (cache)
kubectl apply -f redis-deployment.yaml

# Deploy ChromaDB (vector database)
kubectl apply -f chromadb-deployment.yaml

# Deploy Ollama (LLM)
kubectl apply -f ollama-deployment.yaml

# Deploy Backend (API)
kubectl apply -f backend-deployment.yaml

# Deploy Frontend (Web UI)
kubectl apply -f frontend-deployment.yaml
```

### 4. Enable Auto-scaling

```bash
kubectl apply -f hpa.yaml
```

## Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n agentic-ai

# Check services
kubectl get svc -n agentic-ai

# Check HPAs
kubectl get hpa -n agentic-ai
```

## Access the Application

### Get Frontend URL

```bash
# For LoadBalancer
kubectl get svc frontend -n agentic-ai

# For NodePort (if LoadBalancer not available)
kubectl get nodes -o wide
kubectl get svc frontend -n agentic-ai -o jsonpath='{.spec.ports[0].nodePort}'
```

Access at: `http://<EXTERNAL-IP>` or `http://<NODE-IP>:<NODE-PORT>`

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment backend -n agentic-ai --replicas=5

# Scale frontend
kubectl scale deployment frontend -n agentic-ai --replicas=3
```

### Auto-scaling

HPA will automatically scale based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)

## Monitoring

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n agentic-ai

# Frontend logs
kubectl logs -f deployment/frontend -n agentic-ai

# Ollama logs
kubectl logs -f deployment/ollama -n agentic-ai
```

### Pod Status

```bash
kubectl describe pod <pod-name> -n agentic-ai
```

## Configuration

### Environment Variables

Modify environment variables in deployment files:

- `backend-deployment.yaml`: Backend configuration
- `frontend-deployment.yaml`: Frontend configuration

### Resources

Adjust resource limits in deployment files based on your cluster capacity.

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod <pod-name> -n agentic-ai
kubectl logs <pod-name> -n agentic-ai
```

### Storage Issues

```bash
kubectl get pvc -n agentic-ai
kubectl describe pvc <pvc-name> -n agentic-ai
```

### Network Issues

```bash
kubectl get svc -n agentic-ai
kubectl get endpoints -n agentic-ai
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace agentic-ai

# Or delete individually
kubectl delete -f frontend-deployment.yaml
kubectl delete -f backend-deployment.yaml
kubectl delete -f ollama-deployment.yaml
kubectl delete -f chromadb-deployment.yaml
kubectl delete -f redis-deployment.yaml
kubectl delete -f hpa.yaml
kubectl delete -f pvcs.yaml
kubectl delete -f namespace.yaml
```

## Production Considerations

1. **Secrets Management**: Use Kubernetes Secrets for sensitive data
2. **Ingress**: Configure Ingress for proper routing
3. **TLS**: Enable HTTPS with cert-manager
4. **Monitoring**: Deploy Prometheus and Grafana
5. **Backup**: Regular backups of PVCs
6. **Resource Limits**: Fine-tune based on actual usage
7. **Health Checks**: Customize probe parameters
8. **Network Policies**: Implement security policies

## Advanced Configuration

### Using Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agentic-ai-ingress
  namespace: agentic-ai
spec:
  rules:
  - host: ai.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

### ConfigMaps

Create ConfigMap for configuration:

```bash
kubectl create configmap backend-config \
  --from-file=config.yaml \
  -n agentic-ai
```

## Support

For issues or questions:
- Check logs: `kubectl logs -f <pod> -n agentic-ai`
- Review events: `kubectl get events -n agentic-ai`
- Describe resources: `kubectl describe <resource> -n agentic-ai`
