#!/bin/bash
set -e

echo "🚀 AI Chatbot - Kubernetes Deployment Script"
echo "=============================================="
echo ""

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ docker not found. Please install Docker first."
    exit 1
fi

# Deployment options
echo "Select deployment option:"
echo "1) Local - Kind cluster (recommended for testing)"
echo "2) Local - Minikube"
echo "3) Existing Kubernetes cluster"
echo ""
read -p "Enter option (1-3): " option

case $option in
    1)
        echo ""
        echo "📦 Deploying to Kind cluster..."
        
        # Check if kind exists
        if ! command -v kind &> /dev/null; then
            echo "Installing Kind..."
            curl -Lo /tmp/kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
            chmod +x /tmp/kind
            sudo mv /tmp/kind /usr/local/bin/kind
        fi
        
        # Check if cluster exists
        if ! kind get clusters | grep -q "^ai-chatbot$"; then
            echo "Creating Kind cluster..."
            kind create cluster --name ai-chatbot
        else
            echo "Using existing 'ai-chatbot' cluster"
        fi
        
        CONTEXT="kind-ai-chatbot"
        
        # Build and load image
        echo "Building Docker image..."
        docker build -t devops-chatbot:latest .
        
        echo "Loading image into Kind..."
        kind load docker-image devops-chatbot:latest --name ai-chatbot
        ;;
        
    2)
        echo ""
        echo "📦 Deploying to Minikube..."
        
        if ! command -v minikube &> /dev/null; then
            echo "❌ Minikube not found. Please install Minikube first."
            exit 1
        fi
        
        # Start Minikube if not running
        if ! minikube status &> /dev/null; then
            echo "Starting Minikube..."
            minikube start
        fi
        
        CONTEXT="minikube"
        
        # Build and load image
        echo "Building Docker image..."
        docker build -t devops-chatbot:latest .
        
        echo "Loading image into Minikube..."
        minikube image load devops-chatbot:latest
        ;;
        
    3)
        echo ""
        echo "📦 Deploying to existing Kubernetes cluster..."
        
        # Get current context
        CONTEXT=$(kubectl config current-context)
        echo "Current context: $CONTEXT"
        read -p "Proceed with this context? (y/n): " confirm
        
        if [ "$confirm" != "y" ]; then
            echo "Deployment cancelled."
            exit 0
        fi
        
        echo ""
        echo "⚠️  Note: For production clusters, you need to:"
        echo "  1. Build and push image to a container registry"
        echo "  2. Update k8s/deployment.yaml with the registry image"
        echo ""
        read -p "Have you pushed the image to a registry? (y/n): " pushed
        
        if [ "$pushed" != "y" ]; then
            echo "Please push the image first, then run this script again."
            exit 0
        fi
        ;;
        
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

# Deploy to Kubernetes
echo ""
echo "🔧 Deploying Kubernetes resources..."

# Apply ConfigMap
echo "  → Creating ConfigMap..."
kubectl apply -f k8s/configmap.yaml --context $CONTEXT

# Apply Service
echo "  → Creating Service..."
kubectl apply -f k8s/service.yaml --context $CONTEXT

# Apply Deployment
echo "  → Creating Deployment..."
kubectl apply -f k8s/deployment.yaml --context $CONTEXT

# Wait for deployment
echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=devops-chatbot --timeout=120s --context $CONTEXT

# Get status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Status:"
kubectl get pods -l app=devops-chatbot --context $CONTEXT
echo ""

# Get service info
echo "🌐 Service Information:"
kubectl get svc devops-chatbot --context $CONTEXT
echo ""

# Access instructions
case $option in
    1)
        echo "🔗 Access your application:"
        echo "  → Port forward: kubectl port-forward --context $CONTEXT svc/devops-chatbot 8080:80"
        echo "  → Then open: http://localhost:8080"
        echo ""
        echo "💡 To delete: kind delete cluster --name ai-chatbot"
        ;;
    2)
        echo "🔗 Access your application:"
        echo "  → Run: minikube service devops-chatbot"
        echo "  → Or port forward: kubectl port-forward svc/devops-chatbot 8080:80"
        echo ""
        echo "💡 To delete: kubectl delete -f k8s/"
        ;;
    3)
        echo "🔗 Access your application:"
        echo "  → NodePort: Access via http://<node-ip>:30000"
        echo "  → Port forward: kubectl port-forward svc/devops-chatbot 8080:80"
        echo ""
        echo "💡 To delete: kubectl delete -f k8s/"
        ;;
esac

echo ""
echo "📝 Useful commands:"
echo "  → kubectl logs -l app=devops-chatbot --context $CONTEXT"
echo "  → kubectl describe pod <pod-name> --context $CONTEXT"
echo "  → kubectl get all --context $CONTEXT"
echo ""
