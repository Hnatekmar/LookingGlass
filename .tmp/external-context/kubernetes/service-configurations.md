---
source: Kubernetes Official Documentation
library: Kubernetes
package: kubernetes
topic: Service Configurations
fetched: 2026-02-28T00:00:00Z
official_docs: https://kubernetes.io/docs/concepts/services-networking/service/
---

# Kubernetes Service Configurations

## Overview

Kubernetes Services provide stable network endpoints for accessing pods. They abstract away the dynamic nature of pod IPs and provide load balancing.

## Service Types

### 1. ClusterIP (Default)

**Use Case**: Internal service-to-service communication within the cluster

**Characteristics**:
- Exposes service on cluster-internal IP
- Only accessible from within the cluster
- Best for microservices communication
- No external exposure

**Example**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

**When to Use**:
- Backend APIs
- Database connections
- Internal microservices
- Services that shouldn't be externally accessible

### 2. NodePort

**Use Case**: Expose service on each Node's IP at a static port

**Characteristics**:
- Exposes service on same port across all nodes
- Accessible externally via `<NodeIP>:<NodePort>`
- Port range: 30000-32767
- Creates ClusterIP backend automatically
- Not recommended for production without additional load balancer

**Example**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
      nodePort: 30080
```

**When to Use**:
- Development/testing environments
- Quick external access
- When LoadBalancer is not available
- Simple external exposure needs

**Limitations**:
- Only one service per port
- Limited port range
- Requires node firewall configuration
- No SSL termination
- Not suitable for high-traffic production

### 3. LoadBalancer

**Use Case**: Expose service externally using cloud provider's load balancer

**Characteristics**:
- Creates external load balancer (cloud-specific)
- Assigns external IP address
- Automatically routes traffic to nodes
- Supports multiple services (different ports)
- Best for production web applications

**Example**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

**When to Use**:
- Production web applications
- Public-facing APIs
- When cloud provider load balancer is available
- Need for external DNS integration

**Cloud Provider Implementations**:
- **AWS**: Creates Network Load Balancer or Application Load Balancer
- **GCP**: Creates Google Cloud Load Balancer
- **Azure**: Creates Azure Load Balancer
- **On-premise**: Requires metalLB or similar solution

**Considerations**:
- Cost (cloud provider charges)
- Limited availability (depends on cloud provider)
- May require additional configuration for SSL/TLS
- Can be combined with Ingress for better routing

## Service Configuration Best Practices

### 1. Use Named Ports
```yaml
ports:
  - name: http
    port: 80
    targetPort: http
```

### 2. Specify Protocol Explicitly
```yaml
ports:
  - protocol: TCP
    port: 80
```

### 3. Use Appropriate Selectors
```yaml
selector:
  app: my-app
  version: v1
```

### 4. Configure Session Affinity (if needed)
```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

### 5. Define Multiple Ports
```yaml
ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
```

## Service Type Comparison

| Feature | ClusterIP | NodePort | LoadBalancer |
|---------|-----------|----------|--------------|
| Internal Access | ✅ | ✅ | ✅ |
| External Access | ❌ | ✅ | ✅ |
| Cloud Load Balancer | ❌ | ❌ | ✅ |
| Port Range | Any | 30000-32767 | Any |
| Production Ready | ✅ | ⚠️ | ✅ |
| Cost | Free | Free | Paid (cloud) |

## Recommendations for Web Applications

### Development Environment
- Use **NodePort** for quick access
- Or use `kubectl port-forward` for local testing

### Staging Environment
- Use **LoadBalancer** if available
- Or use **NodePort** with reverse proxy

### Production Environment
- Use **LoadBalancer** for public services
- Use **ClusterIP** for internal services
- Combine with **Ingress** for HTTP/HTTPS routing
- Consider **Ingress Controller** for advanced routing

## Common Patterns

### Microservices Architecture
```yaml
# Frontend - LoadBalancer
type: LoadBalancer
# Backend - ClusterIP
type: ClusterIP
# Database - ClusterIP (no external access)
type: ClusterIP
```

### Multi-tier Application
```yaml
# Load Balancer tier
type: LoadBalancer
  ↓
# Application tier
type: ClusterIP
  ↓
# Data tier
type: ClusterIP
```

## Troubleshooting

### Service Not Accessible
- Check selector labels match pod labels
- Verify targetPort matches container port
- Check network policies
- Verify service endpoints exist

### LoadBalancer Not Getting External IP
- Check cloud provider permissions
- Verify load balancer quota
- Check cloud provider status
- Review events: `kubectl describe service <name>`

### Connection Timeout
- Check firewall rules
- Verify security groups
- Check pod readiness probes
- Review network policies
