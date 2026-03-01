---
source: Kubernetes Official Documentation
library: Kubernetes
package: kubernetes
topic: Health Checks (Probes)
fetched: 2026-02-28T00:00:00Z
official_docs: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
---

# Health Checks: Liveness, Readiness, and Startup Probes

## Overview

Kubernetes probes allow the cluster to monitor and respond to the health of your applications. Properly configured probes ensure high availability and prevent traffic from being routed to unhealthy pods.

## Probe Types

### 1. Liveness Probe

**Purpose**: Determines if the container is running properly

**Behavior**:
- If liveness probe fails, Kubernetes **restarts** the container
- Used to detect deadlocks and application hangs
- Helps recover from application errors

**When to Use**:
- Application can recover from transient failures
- Detect deadlocks or hung processes
- Ensure application responsiveness

### 2. Readiness Probe

**Purpose**: Determines if the container is ready to accept traffic

**Behavior**:
- If readiness probe fails, the pod is **removed from Service endpoints**
- Pod is NOT restarted
- Used to prevent traffic to unready pods

**When to Use**:
- Application needs time to start
- Dependencies aren't ready yet
- Application is under heavy load
- Graceful degradation scenarios

### 3. Startup Probe

**Purpose**: Determines if the application within the container has started

**Behavior**:
- If startup probe fails, Kubernetes **kills and restarts** the container
- Disables liveness and readiness checks until startup succeeds
- Used for slow-starting applications

**When to Use**:
- Legacy applications with long startup times
- Applications that need minutes to initialize
- Prevent premature liveness/reality failures

## Probe Configuration Methods

### 1. HTTP GET Probe

Checks by making an HTTP GET request to the container.

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
    httpHeaders:
    - name: X-Custom-Header
      value: Awesome
  initialDelaySeconds: 3
  periodSeconds: 3
```

**Best For**:
- HTTP/HTTPS applications
- REST APIs
- Web servers

**Example - Complete Pod**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: web
    image: nginx
    ports:
    - containerPort: 80
    livenessProbe:
      httpGet:
        path: /health
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
```

### 2. TCP Socket Probe

Checks by attempting to open a TCP connection to the container.

```yaml
livenessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
```

**Best For**:
- Applications without HTTP endpoints
- Database services
- TCP-based services

**Example**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: redis
spec:
  containers:
  - name: redis
    image: redis:7
    ports:
    - containerPort: 6379
    livenessProbe:
      tcpSocket:
        port: 6379
      initialDelaySeconds: 15
      periodSeconds: 20
    readinessProbe:
      tcpSocket:
        port: 6379
      initialDelaySeconds: 5
      periodSeconds: 10
```

### 3. Exec Probe

Executes a command inside the container.

```yaml
livenessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

**Best For**:
- Complex health checks
- Checking file existence
- Running custom scripts
- Checking application-specific conditions

**Example**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: custom-app
spec:
  containers:
  - name: app
    image: myapp:latest
    livenessProbe:
      exec:
        command:
        - /bin/sh
        - -c
        - nc -z localhost 8080
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      exec:
        command:
        - /bin/sh
        - -c
        - curl -sf http://localhost:8080/ready
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Probe Parameters

### Common Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `initialDelaySeconds` | Seconds after container starts before probing | 0 |
| `periodSeconds` | How often to perform the probe | 10 |
| `timeoutSeconds` | Seconds after which probe times out | 1 |
| `failureThreshold` | Consecutive failures before acting | 3 |
| `successThreshold` | Consecutive successes before considering ready | 1 |

### Startup Probe Specific

| Parameter | Description |
|-----------|-------------|
| `failureThreshold` | Maximum failures before killing container |
| `periodSeconds` | Probe frequency (failureThreshold × period = max startup time) |

**Example**: `failureThreshold: 30` and `periodSeconds: 10` = 5 minutes max startup time

## Best Practices

### 1. Implement Health Endpoints

**HTTP Health Endpoint Example** (Node.js):
```javascript
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

app.get('/ready', (req, res) => {
  // Check database connection, cache, etc.
  if (database.isConnected() && cache.isConnected()) {
    res.status(200).json({ status: 'ready' });
  } else {
    res.status(503).json({ status: 'not ready' });
  }
});
```

**Python Example**:
```python
from flask import Flask, jsonify
import psutil

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent
    }), 200

@app.route('/ready')
def ready():
    # Check dependencies
    if check_database() and check_cache():
        return jsonify({'status': 'ready'}), 200
    return jsonify({'status': 'not ready'}), 503
```

### 2. Configure Appropriate Timing

**Fast-starting application**:
```yaml
livenessProbe:
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3

readinessProbe:
  initialDelaySeconds: 0
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

**Slow-starting application**:
```yaml
startupProbe:
  initialDelaySeconds: 0
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 30  # 5 minutes max startup
```

### 3. Differentiate Liveness and Readiness

**Liveness** - Simple check if app is running:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

**Readiness** - Comprehensive check if app can handle traffic:
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

### 4. Handle Dependencies

**Check database connectivity**:
```yaml
readinessProbe:
  exec:
    command:
    - /bin/sh
    - -c
    - nc -z database-service 5432
  initialDelaySeconds: 10
  periodSeconds: 10
```

**Check external API**:
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
```

### 5. Avoid Common Pitfalls

❌ **Don't check the same endpoint for both probes**
```yaml
# Bad - Same endpoint for liveness and readiness
livenessProbe:
  httpGet:
    path: /health
    port: 8080
readinessProbe:
  httpGet:
    path: /health  # Should be different
    port: 8080
```

✅ **Use different endpoints or logic**
```yaml
# Good - Different endpoints
livenessProbe:
  httpGet:
    path: /health
    port: 8080
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
```

❌ **Don't set initialDelaySeconds too low**
```yaml
# Bad - Might fail before app starts
livenessProbe:
  initialDelaySeconds: 0
```

✅ **Give application time to start**
```yaml
# Good - Allow startup time
livenessProbe:
  initialDelaySeconds: 15
```

## Complete Example: Production Web Application

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
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          successThreshold: 1
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
          successThreshold: 1
        startupProbe:
          httpGet:
            path: /startup
            port: 8080
          initialDelaySeconds: 0
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 30
          successThreshold: 1
        env:
        - name: NODE_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "info"
```

## Troubleshooting

### Pod Restarting Continuously

1. Check liveness probe configuration
2. Verify health endpoint exists and responds correctly
3. Increase `initialDelaySeconds`
4. Check container logs: `kubectl logs <pod-name>`
5. Describe pod for probe events: `kubectl describe pod <pod-name>`

### Pod Not Receiving Traffic

1. Check readiness probe status: `kubectl get pod <name> -o wide`
2. Verify readiness endpoint responds with 200
3. Check service endpoints: `kubectl get endpoints <service-name>`
4. Review probe timeout settings
5. Check resource limits (might be throttling)

### Startup Probe Not Completing

1. Increase `failureThreshold` or `periodSeconds`
2. Check application startup logs
3. Verify startup endpoint exists
4. Consider reducing application startup time
5. Check resource constraints

### Common Error Messages

**"Liveness probe failed"**:
- Container is unresponsive
- Check application logs
- Verify health endpoint

**"Readiness probe failed"**:
- Pod removed from service endpoints
- Check dependencies
- Verify readiness endpoint

**"Back-off restarting failed container"**:
- Liveness probe failing repeatedly
- Review probe configuration
- Check application health

## Monitoring Probes

### View Probe Status
```bash
# Check pod conditions
kubectl get pod <pod-name> -o jsonpath='{.status.conditions}'

# Watch pod status
kubectl get pod <pod-name> -w

# Check probe events
kubectl describe pod <pod-name> | grep -A 5 "Liveness\|Readiness"
```

### Debug Probes
```bash
# Execute probe command manually
kubectl exec <pod-name> -- curl -v http://localhost:8080/health

# Check container logs
kubectl logs <pod-name> -c <container-name>

# Port-forward for testing
kubectl port-forward pod/<pod-name> 8080:8080
curl http://localhost:8080/health
```

## Recommendations by Application Type

### Web Application (HTTP)
- Use HTTP probes
- `/health` for liveness
- `/ready` for readiness
- Initial delay: 10-30 seconds

### Database Service
- Use TCP probes
- Check port connectivity
- Initial delay: 15-30 seconds

### Legacy Application
- Use startup probe
- Long failure threshold
- Exec probe if no HTTP endpoint

### Microservice
- HTTP probes with dependency checks
- Readiness includes DB/cache checks
- Liveness checks app responsiveness
