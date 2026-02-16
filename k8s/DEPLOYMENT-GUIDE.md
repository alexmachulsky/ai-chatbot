# Kubernetes Deployment Guide

## Prerequisites

- `kubectl` installed and configured
- Docker installed (for building images)
- Access to a Kubernetes cluster

## Option 1: Local Testing with Kind

### Install Kind
```bash
curl -Lo /tmp/kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x /tmp/kind
sudo mv /tmp/kind /usr/local/bin/kind
```

### Create Cluster and Deploy
```bash
# Create Kind cluster
kind create cluster --name ai-chatbot

# Build and load Docker image
docker build -t devops-chatbot:latest .
kind load docker-image devops-chatbot:latest --name ai-chatbot

# Deploy to Kubernetes
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods
kubectl get svc

# Test the application
kubectl port-forward svc/devops-chatbot 8080:80
# Access at http://localhost:8080
```

## Option 2: Minikube (Alternative)

```bash
# Start Minikube
minikube start

# Build and load image
docker build -t devops-chatbot:latest .
minikube image load devops-chatbot:latest

# Deploy
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml

# Access the service
minikube service devops-chatbot
```

## Option 3: Production Kubernetes (EKS/GKE/AKS)

### 1. Build and Push Image to Registry

```bash
# Build image with tag
docker build -t your-registry/devops-chatbot:v1.1.0 .

# Push to container registry
docker push your-registry/devops-chatbot:v1.1.0
```

### 2. Update deployment.yaml

Edit `k8s/deployment.yaml` and change:
```yaml
image: devops-chatbot:latest
imagePullPolicy: IfNotPresent
```
To:
```yaml
image: your-registry/devops-chatbot:v1.1.0
imagePullPolicy: Always
```

### 3. Deploy with Ollama in Kubernetes

If you want to run Ollama inside the cluster:

```bash
# Deploy Ollama first
kubectl apply -f k8s/ollama-deployment.yaml

# Wait for Ollama to be ready
kubectl wait --for=condition=ready pod -l app=ollama --timeout=300s

# Update OLLAMA_URL in deployment.yaml to use internal service
# Change from: http://192.168.18.241:11434
# To: http://ollama:11434

# Deploy the chatbot
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
```

### 4. Verify Deployment

```bash
# Check all resources
kubectl get all

# Check pod logs
kubectl logs -l app=devops-chatbot

# Test health endpoint
kubectl port-forward svc/devops-chatbot 8080:80
curl http://localhost:8080/api/health
```

### 5. Expose Service

**NodePort (already configured):**
```bash
# Service is exposed on port 30000
kubectl get svc devops-chatbot
# Access at http://<node-ip>:30000
```

**LoadBalancer (for cloud):**
```bash
# Edit k8s/service.yaml and change type from NodePort to LoadBalancer
kubectl apply -f k8s/service.yaml
kubectl get svc devops-chatbot  # Wait for EXTERNAL-IP
```

**Ingress (recommended for production):**
```yaml
# Create ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: devops-chatbot
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
  - host: chatbot.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: devops-chatbot
            port:
              number: 80
```

## Configuration

### Environment Variables

Edit `k8s/configmap.yaml` or set directly in `k8s/deployment.yaml`:

```yaml
env:
- name: OLLAMA_MODEL
  value: "llama3.2:1b"  # Change model
- name: GOOGLE_API_KEY
  value: "your-api-key"  # For Web Mode
- name: GOOGLE_CSE_ID
  value: "your-cse-id"
```

### Secrets (recommended for sensitive data)

```bash
# Create secret for Google API
kubectl create secret generic chatbot-secrets \
  --from-literal=GOOGLE_API_KEY=your-key \
  --from-literal=GOOGLE_CSE_ID=your-cse-id

# Reference in deployment:
envFrom:
- secretRef:
    name: chatbot-secrets
```

## Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment devops-chatbot --replicas=3

# Auto-scaling
kubectl autoscale deployment devops-chatbot --min=2 --max=10 --cpu-percent=80
```

## Monitoring

```bash
# Watch pods
kubectl get pods -w

# View logs from all pods
kubectl logs -l app=devops-chatbot --tail=100 -f

# Describe pod for troubleshooting
kubectl describe pod <pod-name>

# Execute commands in pod
kubectl exec -it <pod-name> -- /bin/bash
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/

# Or delete specific resources
kubectl delete deployment devops-chatbot
kubectl delete service devops-chatbot
kubectl delete configmap devops-chatbot-config

# Delete Kind cluster
kind delete cluster --name ai-chatbot
```

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Can't reach Ollama
- Verify OLLAMA_URL is correct
- Check if Ollama service is running: `kubectl get svc ollama`
- Test connectivity: `kubectl exec -it <pod-name> -- curl http://ollama:11434`

### Image pull errors
- Ensure image is built and available
- For Kind/Minikube: Load image into cluster
- For production: Push to registry and verify credentials

### Health check failures
- Check if Ollama is reachable
- Review pod logs: `kubectl logs <pod-name>`
- Test health endpoint manually: `kubectl port-forward <pod-name> 5000:5000`

## Production Checklist

- [ ] Use container registry (ECR, GCR, ACR, Docker Hub)
- [ ] Set resource limits and requests
- [ ] Configure horizontal pod autoscaling
- [ ] Set up ingress with TLS/SSL
- [ ] Use secrets for sensitive data
- [ ] Configure persistent storage for RAG database
- [ ] Set up monitoring and logging
- [ ] Configure network policies
- [ ] Use namespaces for isolation
- [ ] Implement backup strategy
