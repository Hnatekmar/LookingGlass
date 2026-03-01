---
source: Kubernetes Official Documentation
library: Kubernetes
package: kubernetes
topic: Resource Requests and Limits
fetched: 2026-02-28T00:00:00Z
official_docs: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
---

# Resource Requests and Limits

## Overview

Kubernetes uses resource requests and limits to schedule pods efficiently and prevent resource exhaustion. Proper resource configuration is critical for cluster stability and application performance.

## Resource Types

### CPU

**Units**:
- `1` = 1 CPU core
- `0.5` = 500 millicores (half a core)
- `100m` = 100 millicores (0.1 core)

**Syntax**:
```yaml
resources:
  requests:
    cpu: "500m"  # or "0.5"
  limits:
    cpu: "1000m" # or "1"
```

**Behavior**:
- Guaranteed minimum (requests)
- Hard cap (limits)
- Throttled if exceeding limit (not killed)

### Memory

**Units**:
- `Mi` = Mebibytes (1024^2 bytes)
- `Gi` = Gibibytes (1024^3 bytes)
- `M` = Megabytes (1000^2 bytes)
- `G` = Gigabytes (1000^3 bytes)

**Syntax**:
```yaml
resources:
  requests:
    memory: "128Mi"
  limits:
    memory: "256Mi"
```

**Behavior**:
- Guaranteed minimum (requests)
- Hard cap (limits)
- OOM killed if exceeding limit

## Resource Configuration

### Basic Configuration

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: nginx
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "500m"
```

### Complete Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web
        image: web-app:1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Resource Classes

### 1. Guaranteed (Highest Priority)

**Configuration**:
- Requests = Limits for both CPU and memory
- Highest QoS class
- Last to be evicted

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**Use Case**:
- Critical production services
- Latency-sensitive applications
- Database services

### 2. Burstable (Medium Priority)

**Configuration**:
- Requests < Limits
- Medium QoS class
- Can burst up to limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "1000m"
```

**Use Case**:
- Most web applications
- Services with variable load
- Non-critical services

### 3. Best Effort (Lowest Priority)

**Configuration**:
- No requests or limits specified
- Lowest QoS class
- First to be evicted

```yaml
resources:
  # No requests or limits
```

**Use Case**:
- Development/testing
- Batch jobs
- Non-critical workloads

## Recommended Resource Values

### Web Applications (Node.js, Python, Java)

**Small/Medium Traffic**:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**High Traffic**:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Backend APIs

**Standard**:
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```

**Database-Heavy**:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Database Services

**PostgreSQL/MySQL**:
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

**Redis**:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Frontend (Nginx, Static)

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

### Worker/Background Jobs

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "2000m"
```

## Best Practices

### 1. Start with Requests, Add Limits Later

**Initial Setup**:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  # No limits initially
```

**After Monitoring**:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"  # 2x average usage
    cpu: "500m"      # 2x average usage
```

### 2. Monitor and Adjust

**Check current usage**:
```bash
# View resource usage
kubectl top pods

# View node usage
kubectl top nodes

# Check historical usage (requires metrics-server)
kubectl describe pod <pod-name>
```

**Adjust based on metrics**:
- If hitting limits frequently: Increase limits
- If consistently underutilized: Decrease requests
- If OOM killed: Increase memory limits

### 3. Set Appropriate Ratios

**Memory**:
- Requests: 50-75% of expected usage
- Limits: 150-200% of requests
- Example: Request 256Mi, Limit 512Mi

**CPU**:
- Requests: 50-75% of average usage
- Limits: 200-300% of requests (allow bursting)
- Example: Request 250m, Limit 1000m

### 4. Use Namespace Defaults

**LimitRange**:
```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
spec:
  limits:
  - default:
      memory: "512Mi"
      cpu: "500m"
    defaultRequest:
      memory: "256Mi"
      cpu: "250m"
    type: Container
```

**Apply to namespace**:
```bash
kubectl apply -f limitrange.yaml
```

### 5. Implement Resource Quotas

**Quota per namespace**:
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
```

### 6. Consider Pod Disruption

**Memory**:
- Set limits to prevent OOM
- Monitor for memory leaks
- Use readiness probes

**CPU**:
- Allow bursting for traffic spikes
- Use HPA for scaling
- Monitor CPU throttling

### 7. Test with Realistic Load

**Before production**:
1. Load test with expected traffic
2. Monitor resource usage
3. Adjust based on actual metrics
4. Set appropriate limits

## Common Scenarios

### Scenario 1: Memory OOM

**Problem**: Pod frequently OOM killed

**Solution**:
```yaml
# Increase memory limits
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "1Gi"  # Increased from 512Mi
```

**Alternative**:
- Optimize application memory usage
- Reduce concurrency
- Add more replicas

### Scenario 2: CPU Throttling

**Problem**: High latency due to CPU throttling

**Solution**:
```yaml
# Increase CPU limits
resources:
  requests:
    cpu: "500m"
  limits:
    cpu: "2000m"  # Increased from 1000m
```

**Alternative**:
- Optimize code performance
- Add more replicas
- Use horizontal scaling

### Scenario 3: Over-provisioned

**Problem**: Resources allocated but not used

**Solution**:
```yaml
# Reduce resource requests
resources:
  requests:
    memory: "128Mi"   # Reduced from 256Mi
    cpu: "100m"       # Reduced from 250m
  limits:
    memory: "256Mi"   # Reduced from 512Mi
    cpu: "500m"       # Reduced from 1000m
```

## Monitoring Resources

### Check Pod Resource Usage

```bash
# View current usage
kubectl top pod <pod-name>

# View all pods
kubectl top pods --all-namespaces

# View node usage
kubectl top nodes
```

### Check Resource Events

```bash
# Describe pod for resource events
kubectl describe pod <pod-name>

# Look for:
# - OOMKilled events
# - CPU throttling
# - Pending due to resources
```

### View Resource Requests/Limits

```bash
# View all pods with resources
kubectl get pods -o custom-columns=NAME:.metadata.name,CPU-REQ:.spec.containers[*].resources.requests.cpu,CPU-LIM:.spec.containers[*].resources.limits.cpu,MEM-REQ:.spec.containers[*].resources.requests.memory,MEM-LIM:.spec.containers[*].resources.limits.memory
```

## Troubleshooting

### Pod Pending

**Check**:
```bash
kubectl describe pod <pod-name>
```

**Common Causes**:
- Insufficient cluster resources
- Node taints/tolerations
- Node selectors/affinity
- Resource quotas exceeded

**Solutions**:
- Add more nodes
- Adjust resource requests
- Check node selectors
- Review resource quotas

### Pod Crashing (OOMKilled)

**Check**:
```bash
kubectl describe pod <pod-name> | grep -i oom
kubectl logs <pod-name> --previous
```

**Solutions**:
- Increase memory limits
- Optimize application memory
- Add memory profiling
- Reduce concurrency

### High CPU Throttling

**Check**:
```bash
kubectl top pod <pod-name>
# Look for CPU usage near limit
```

**Solutions**:
- Increase CPU limits
- Optimize CPU-intensive code
- Add more replicas
- Use horizontal scaling

### Resource Quota Exceeded

**Check**:
```bash
kubectl describe quota -n <namespace>
```

**Solutions**:
- Request quota increase
- Reduce resource requests
- Delete unused resources
- Optimize existing deployments

## Recommendations Summary

### For Web Applications

| Component | Request | Limit |
|-----------|---------|-------|
| Memory | 256Mi | 512Mi |
| CPU | 250m | 500m |

### For APIs

| Component | Request | Limit |
|-----------|---------|-------|
| Memory | 128Mi | 256Mi |
| CPU | 100m | 500m |

### For Databases

| Component | Request | Limit |
|-----------|---------|-------|
| Memory | 1Gi | 2Gi |
| CPU | 500m | 1000m |

### For Frontend

| Component | Request | Limit |
|-----------|---------|-------|
| Memory | 64Mi | 128Mi |
| CPU | 50m | 200m |

## Key Takeaways

1. **Always set requests** for scheduling
2. **Set limits** to prevent resource exhaustion
3. **Monitor usage** and adjust accordingly
4. **Start conservative**, scale as needed
5. **Use QoS classes** appropriately
6. **Implement quotas** per namespace
7. **Test under load** before production
8. **Review regularly** as application evolves
