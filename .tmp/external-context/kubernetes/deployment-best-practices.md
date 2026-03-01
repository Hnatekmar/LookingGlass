---
source: Kubernetes Official Documentation
library: Kubernetes
package: kubernetes
topic: Deployment Best Practices
fetched: 2026-02-28T00:00:00Z
official_docs: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
---

# Kubernetes Deployment Best Practices for Web Applications

## Overview

Deployments provide declarative updates for Pods and ReplicaSets. They are the recommended way to deploy stateless web applications in Kubernetes.

## Key Best Practices

### 1. Use Declarative Configuration
- Define deployments in YAML manifests
- Use `kubectl apply` for declarative updates
- Version control your deployment manifests

### 2. Set Appropriate Replica Count
- Always run multiple replicas for production (minimum 2-3)
- Use HorizontalPodAutoscaler for dynamic scaling
- Consider your availability requirements

### 3. Configure Rolling Updates
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```
- `maxSurge`: Maximum number of pods above desired count
- `maxUnavailable`: Maximum number of pods that can be unavailable
- Set `maxUnavailable: 0` for zero-downtime deployments

### 4. Use Pod Disruption Budgets
- Protect against voluntary disruptions
- Ensure minimum availability during maintenance
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-app-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web-app
```

### 5. Label Your Resources Consistently
- Use consistent labeling across all resources
- Follow recommended label conventions
- Enable easy resource discovery and management

### 6. Implement Health Checks
- Always configure liveness and readiness probes
- Use startup probes for slow-starting applications
- Prevent traffic to unhealthy pods

### 7. Configure Resource Requests and Limits
- Set CPU and memory requests for scheduling
- Set limits to prevent resource exhaustion
- Match requests to actual application needs

### 8. Use Namespaces for Organization
- Separate environments (dev, staging, prod)
- Isolate different applications
- Apply resource quotas per namespace

### 9. Implement Proper Image Management
- Use specific image tags (avoid `latest`)
- Use image pull policies appropriately
- Scan images for vulnerabilities

### 10. Configure Pod Anti-Affinity
- Spread replicas across nodes for high availability
```yaml
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: web-app
          topologyKey: kubernetes.io/hostname
```

## Deployment Strategy Recommendations

### Rolling Update (Recommended for most web apps)
- Default strategy
- Zero-downtime deployments
- Gradual rollout of changes

### Recreate
- Use for stateful applications
- All pods terminated before new ones created
- Causes temporary downtime

### Blue-Green
- Deploy new version alongside old
- Switch traffic when ready
- Requires additional resources

### Canary
- Gradually route traffic to new version
- Monitor metrics before full rollout
- Requires service mesh or advanced routing

## Common Mistakes to Avoid

1. **No resource limits**: Can cause node resource exhaustion
2. **Missing health checks**: Kubernetes can't detect unhealthy pods
3. **Single replica**: No high availability
4. **Using `latest` tag**: Unpredictable deployments
5. **No PodDisruptionBudget**: Maintenance can take down all pods
6. **Ignoring pod topology**: All replicas on same node
7. **No logging/monitoring**: Can't troubleshoot issues

## Security Best Practices

- Run containers as non-root
- Use security contexts
- Implement network policies
- Use secrets for sensitive data
- Regular security updates

## Monitoring Recommendations

- Monitor deployment status
- Track replica availability
- Set up alerts for failures
- Monitor resource utilization
- Track rollout progress
