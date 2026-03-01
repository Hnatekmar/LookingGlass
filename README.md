# Looking Glass

An intelligent image annotation service that performs OCR (Optical Character Recognition) and optional translation using Large Language Models (LLMs). Perfect for extracting text from images, manga/comic translation workflows, and automated document processing.

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Local Development

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd looking-glass
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your model configurations
   ```

4. Run the server:
   ```bash
   uv run fastapi run main.py
   # or
   uv run uvicorn main:app --reload
   ```

5. Install the browser extension:
   - Copy `./image_annotator_content_script.js` to Violentmonkey/Greasemonkey
   - Adjust URL in the script if server is on another machine

6. Start using:
   - Right-click on any image to use the annotation and translation feature

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t looking-glass .

# Run with environment variables
docker run -p 8000:8000 \
  -e IMAGE_MODEL=qwen3-8b-instruct \
  -e TRANSLATION_MODEL=nemotron-3-nano \
  -e IMAGE_MODEL_URL=https://your-model-url.com/v1 \
  -e TRANSLATION_MODEL_URL=https://your-translation-url.com/v1 \
  looking-glass
```

## ☸️ Kubernetes Deployment (Helm)

### Prerequisites

- Kubernetes cluster (v1.25+)
- Helm v3.0+
- (Optional) Ingress controller for external access

### Chart Structure

```
charts/looking-glass/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration
├── values.schema.json      # JSON schema for validation
└── templates/
    ├── _helpers.tpl        # Template helpers
    ├── namespace.yaml      # Optional namespace
    ├── configmap.yaml      # Non-sensitive configuration
    ├── secret.yaml         # Sensitive configuration
    ├── deployment.yaml     # Application deployment
    ├── service.yaml        # Service definition
    ├── ingress.yaml        # Ingress configuration
    ├── pdb.yaml            # PodDisruptionBudget
    ├── serviceaccount.yaml # ServiceAccount
    └── NOTES.txt           # Post-install notes
```

### Installation

1. **Basic installation** (requires setting secrets via values file or CLI):

   ```bash
   helm install looking-glass ./charts/looking-glass \
     --namespace looking-glass \
     --create-namespace \
     --set secrets.imageModel="qwen3-8b-instruct" \
     --set secrets.translationModel="nemotron-3-nano" \
     --set secrets.imageModelUrl="https://your-model-url.com/v1" \
     --set secrets.translationModelUrl="https://your-translation-url.com/v1"
   ```

2. **Using a custom values file**:

   Create `values-production.yaml`:
   ```yaml
   replicaCount: 3
   
   secrets:
     imageModel: "qwen3-8b-instruct"
     translationModel: "nemotron-3-nano"
     imageModelUrl: "https://your-model-url.com/v1"
     translationModelUrl: "https://your-translation-url.com/v1"
   
   resources:
     limits:
       cpu: 500m
       memory: 512Mi
     requests:
       cpu: 100m
       memory: 128Mi
   
   ingress:
     enabled: true
     className: "nginx"
     hosts:
       - host: looking-glass.example.com
         paths:
           - path: /
             pathType: Prefix
     tls:
       - secretName: looking-glass-tls
         hosts:
           - looking-glass.example.com
   ```

   Then install:
   ```bash
   helm install looking-glass ./charts/looking-glass \
     -f values-production.yaml \
     --namespace looking-glass \
     --create-namespace
   ```

3. **Accessing the service**:

   - **ClusterIP** (default): Port-forward to access locally
     ```bash
     kubectl port-forward svc/looking-glass 8000:8000 -n looking-glass
     ```
   
   - **Ingress**: Access via configured host (e.g., `https://looking-glass.example.com`)

   - **API Documentation**: Visit `/docs` for Swagger UI

### Configuration Reference

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Docker image repository | `looking-glass` |
| `image.tag` | Image tag | `Chart.AppVersion` |
| `config.canvasWidth` | Canvas width for image processing | `"1000"` |
| `config.canvasHeight` | Canvas height for image processing | `"1000"` |
| `config.defaultTranslateLanguage` | Default translation target language | `"english"` |
| `config.port` | Server port | `"8000"` |
| `secrets.imageModel` | **Required** - Image model name | `""` |
| `secrets.translationModel` | **Required** - Translation model name | `""` |
| `secrets.imageModelUrl` | **Required** - Image model API URL | `""` |
| `secrets.translationModelUrl` | **Required** - Translation model API URL | `""` |
| `resources.limits` | Resource limits | `cpu: 500m, memory: 512Mi` |
| `resources.requests` | Resource requests | `cpu: 100m, memory: 128Mi` |
| `ingress.enabled` | Enable ingress | `false` |
| `pdb.enabled` | Enable PodDisruptionBudget | `false` |
| `namespace.create` | Create namespace | `false` |

### Upgrading

```bash
helm upgrade looking-glass ./charts/looking-glass \
  -f values-production.yaml \
  --namespace looking-glass
```

### Uninstalling

```bash
helm uninstall looking-glass --namespace looking-glass
```

## 🔄 ArgoCD Deployment

### Prerequisites

- ArgoCD installed in your Kubernetes cluster
- Git repository containing this chart (or chart repository)

### Option 1: Git-Based Deployment (Recommended)

1. **Create an ArgoCD Application**:

   Save `argocd-application.yaml`:
   ```yaml
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: looking-glass
     namespace: argocd  # ArgoCD namespace
   spec:
     project: default
   
     # Source of the application manifests
     source:
       repoURL: https://github.com/your-org/looking-glass.git  # Change to your repo
       targetRevision: HEAD  # Or specific branch/tag
       path: charts/looking-glass
   
     # Destination cluster and namespace
     destination:
       server: https://kubernetes.default.svc
       namespace: looking-glass
   
     # Sync policy
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
       syncOptions:
         - CreateNamespace=true
   ```

2. **Apply the ArgoCD Application**:
   ```bash
   kubectl apply -f argocd-application.yaml
   ```

3. **Configure values via ConfigMap** (optional, for GitOps):
   
   Create `argocd-values.yaml`:
   ```yaml
   apiVersion: argoproj.io/v1alpha1
   kind: Application
   metadata:
     name: looking-glass
     namespace: argocd
   spec:
     project: default
   
     source:
       repoURL: https://github.com/your-org/looking-glass.git
       targetRevision: HEAD
       path: charts/looking-glass
       # Override values directly in the Application
       helm:
         values: |
           replicaCount: 3
           
           secrets:
             imageModel: "qwen3-8b-instruct"
             translationModel: "nemotron-3-nano"
             imageModelUrl: "https://your-model-url.com/v1"
             translationModelUrl: "https://your-translation-url.com/v1"
           
           resources:
             limits:
               cpu: 500m
               memory: 512Mi
             requests:
               cpu: 100m
               memory: 128Mi
           
           ingress:
             enabled: true
             className: "nginx"
             hosts:
               - host: looking-glass.example.com
                 paths:
                   - path: /
                     pathType: Prefix
   
     destination:
       server: https://kubernetes.default.svc
       namespace: looking-glass
   
     syncPolicy:
       automated:
         prune: true
         selfHeal: true
       syncOptions:
         - CreateNamespace=true
   ```

### Option 2: Using External Secrets (Production)

For production environments, use external secret management (e.g., External Secrets Operator, Vault):

1. **Disable chart's built-in secrets**:
   ```yaml
   # In your values file
   secrets:
     imageModel: ""  # Leave empty
     translationModel: ""
     imageModelUrl: ""
     translationModelUrl: ""
   ```

2. **Create ExternalSecret resource**:
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: ExternalSecret
   metadata:
     name: looking-glass-secrets
     namespace: looking-glass
   spec:
     refreshInterval: 1h
     secretStoreRef:
       kind: ClusterSecretStore
       name: vault-backend
     target:
       name: looking-glass-secrets
     data:
       - secretKey: IMAGE_MODEL
         remoteRef:
           key: looking-glass
           property: image_model
       - secretKey: TRANSLATION_MODEL
         remoteRef:
           key: looking-glass
           property: translation_model
       - secretKey: IMAGE_MODEL_URL
         remoteRef:
           key: looking-glass
           property: image_model_url
       - secretKey: TRANSLATION_MODEL_URL
         remoteRef:
           key: looking-glass
           property: translation_model_url
   ```

### ArgoCD Dashboard

Access the ArgoCD UI to monitor deployment status:

```bash
# Port-forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `IMAGE_MODEL` | **Yes** | Name of the OCR/image model | `qwen3-8b-instruct` |
| `TRANSLATION_MODEL` | **Yes** | Name of the translation model | `nemotron-3-nano` |
| `IMAGE_MODEL_URL` | **Yes** | API endpoint for image model | `https://llm.example.com/v1` |
| `TRANSLATION_MODEL_URL` | **Yes** | API endpoint for translation model | `https://llm.example.com/v1` |
| `CANVAS_WIDTH` | No | Canvas width for processing | `1000` |
| `CANVAS_HEIGHT` | No | Canvas height for processing | `1000` |
| `DEFAULT_TRANSLATE_LANGUAGE` | No | Default target language | `english` |
| `PORT` | No | Server port | `8000` |

### API Endpoints

- `GET /` - Service information and available endpoints
- `GET /health` - Health check endpoint for monitoring
  - Response: `{"status": "healthy", "service": "Image Annotator Backend", "version": "1.0.0"}`
  
- `POST /translate/` - Text translation
  - Body: `{"text": "string"}`
  - Query: `target_language` (default: "english")
  
- `POST /image/annotate/` - Image annotation
  - Form data: `data` (image file)
  - Query: `translate` (bool), `translate_language` (string)

- `GET /docs` - Swagger UI documentation

## 🔒 Security Considerations

1. **Secrets Management**: Never commit secrets to version control. Use:
   - Helm secrets with encrypted values
   - External secrets operators (Vault, AWS Secrets Manager, etc.)
   - Kubernetes Secrets with RBAC

2. **Network Security**:
   - Use HTTPS for all API endpoints
   - Implement network policies to restrict access
   - Use ingress controllers with TLS termination

3. **Pod Security**:
   - Non-root user execution (configured by default)
   - Read-only root filesystem
   - Dropped capabilities

## 📊 Monitoring

### Health Checks

The chart includes configured health probes:

- **Liveness Probe**: Checks `/health` endpoint every 10s
- **Readiness Probe**: Checks `/health` endpoint every 5s

Adjust probe settings in `values.yaml` as needed.

### Logs

```bash
# View pod logs
kubectl logs -f deployment/looking-glass -n looking-glass

# View previous logs (after restart)
kubectl logs -f deployment/looking-glass -n looking-glass --previous
```

## 🛠️ Troubleshooting

### Common Issues

1. **Pods stuck in Pending state**:
   ```bash
   kubectl describe pod <pod-name> -n looking-glass
   # Check for resource constraints or node selector issues
   ```

2. **CrashLoopBackOff**:
   ```bash
   kubectl logs deployment/looking-glass -n looking-glass --previous
   # Check for configuration errors or missing secrets
   ```

3. **Health check failures**:
   - Verify the `/docs` endpoint is accessible
   - Check resource limits (may be too low)
   - Review application logs for errors

## 📝 License

[Your License Here]

## 🤝 Contributing

[Your Contributing Guidelines Here]
