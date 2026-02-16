# AI ChatBot 🤖

An intelligent AI-powered chatbot application that can assist with any topic - from technology and science to business and everyday questions. Built with Python Flask, Ollama (local LLM), Docker, and Kubernetes.

![AI ChatBot](https://img.shields.io/badge/AI-ChatBot-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue)

## 🌟 Features

- **AI-Powered Responses**: Uses Ollama with Llama 3.1 8B for intelligent assistance across any topic (100% free, runs locally)
- **Modern UI**: Clean, responsive chat interface with smooth animations and glassmorphism effects
- **Conversation History**: Maintains context across multiple messages
- **Streaming Responses**: Token-by-token output for faster perceived response time
- **Model Switcher**: Choose installed Ollama models directly from the UI
- **RAG Mode (Document Grounding)**: Paste long text directly in chat to auto-index and retrieve grounded context
- **Live Web Lookup Mode**: Optional Google search grounding for fresher, time-sensitive answers
- **General Knowledge**: Can discuss technology, science, business, arts, health, and much more
- **Production Ready**: Containerized with Docker and deployable to Kubernetes
- **Health Checks**: Built-in health endpoints for monitoring
- **Security**: Non-root container user, environment variable management
- **No API Keys**: Runs completely locally with Ollama - no external API dependencies
- **High Quality Responses**: 8B parameter model provides detailed, helpful answers

## 🛠️ Tech Stack

### Backend
- **Python 3.11** - Application runtime
- **Flask** - Web framework
- **Ollama** - Local LLM server (Llama 3.1 8B model - 4.9GB)
- **Gunicorn** - Production WSGI server

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **JavaScript (ES6+)** - Interactive chat functionality
- **Font Awesome** - Icons

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Local orchestration
- **Kubernetes** - Production orchestration
- **GitHub Actions** - CI/CD pipeline
- **Trivy** - Security scanning

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- At least 4GB of RAM (for Ollama)

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alexmachulsky/ai-chatbot.git
   cd ai-chatbot
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env to customize Ollama settings if needed
   ```

3. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the chatbot**:
   Open your browser and navigate to `http://localhost:5000`

### Docker Compose Deployment (Recommended for Local/Testing)

1. **Build and run with Docker Compose** (includes Ollama):
   ```bash
   docker compose up -d
   ```

   This will:
   - Start the Ollama server container
   - Pull the Llama 3.1 8B model (first run takes 2-3 minutes)
   - Start the Flask chatbot application

2. **Pull the Ollama model** (if not already pulled):
   ```bash
   docker exec ollama-server ollama pull llama3.1:8b
   ```

3. **Access the chatbot**:
   Open `http://localhost:5000`

4. **View logs**:
   ```bash
   docker compose logs -f chatbot
   docker compose logs -f ollama
   ```

5. **Stop the containers**:
   ```bash
   docker compose down
   ```

### Kubernetes Deployment (Production-Ready)

The chatbot supports full Kubernetes deployment with high availability and scalability features.

#### Prerequisites
- Kubernetes cluster (tested with Minikube v1.35.0)
- kubectl configured
- Docker for building images
- Ollama running (via Docker Compose recommended)

#### Quick Deploy

1. **Start Ollama** (via Docker Compose for better resource management):
   ```bash
   docker-compose up -d ollama
   docker exec ollama-server ollama pull llama3.1:8b
   ```

2. **Build the image** (for Minikube):
   ```bash
   eval $(minikube docker-env)
   docker build -t ai-chatbot:latest .
   ```

3. **Deploy to Kubernetes**:
   ```bash
   cd k8s
   kubectl apply -f configmap.yaml
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   ```

4. **Wait for pods to be ready**:
   ```bash
   kubectl wait --for=condition=ready pod -l app=devops-chatbot --timeout=60s
   ```

5. **Access the application**:
   ```bash
   # Via port-forward (development)
   kubectl port-forward svc/devops-chatbot 8888:80
   # Access at http://localhost:8888
   
   # Via NodePort (network access)
   minikube service devops-chatbot --url
   ```

#### Kubernetes Features

- **High Availability**: 2 replicas with automatic failover
- **Health Checks**: Liveness and readiness probes
- **Resource Management**: CPU and memory limits
- **Session Affinity**: Maintains user sessions
- **Scalability**: Easy horizontal scaling with `kubectl scale`
- **Rolling Updates**: Zero-downtime deployments

#### Monitoring
```bash
# Check pod status
kubectl get pods -l app=devops-chatbot

# View logs
kubectl logs -l app=devops-chatbot -f

# Check resource usage
kubectl top pods -l app=devops-chatbot
```

For detailed Kubernetes deployment instructions, see [k8s/README.md](k8s/README.md)

## 📋 API Endpoints

### POST /api/chat
Send a message to the chatbot.

**Request**:
```json
{
  "message": "What is photosynthesis?",
  "history": []
}
```

### POST /api/chat/stream
Stream chatbot tokens as newline-delimited JSON events.

**Request**:
```json
{
   "message": "What does Kubernetes use?",
   "history": [],
   "model": "llama3.2:1b",
   "rag_enabled": true,
   "web_enabled": true
}
```

### GET /api/models
Returns installed Ollama model names for the model picker.

### GET /api/web/status
Returns whether Google web lookup is configured.

### POST /api/rag/upload
Upload one document (txt, md, csv, log, json, yaml, yml) into RAG memory.

### GET /api/rag/status
Get current RAG document and chunk counts.

### POST /api/rag/clear
Clear loaded RAG documents from in-memory store.

**Response**:
```json
{
  "message": "Photosynthesis is the process by which...",
  "success": true
}
```

### GET /api/health
Health check endpoint for monitoring.

**Response**:
```json
{
  "status": "healthy",
  "service": "devops-chatbot"
}
```

## 🎯 Use Cases

The AI ChatBot can help with:

- **Technology & Programming**: Coding questions, debugging, best practices, frameworks
- **Science & Mathematics**: Explanations, problem-solving, research concepts
- **Business & Finance**: Strategy, analysis, market insights, career advice
- **Arts & Literature**: Creative writing, analysis, recommendations
- **Health & Wellness**: General information, fitness tips, nutrition basics
- **Education**: Learning assistance, explanations, study help
- **General Knowledge**: History, geography, current events, and more

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OLLAMA_URL` | Ollama server URL | No | `http://ollama:11434` |
| `OLLAMA_MODEL` | Ollama model to use | No | `llama3.2:1b` |
| `OLLAMA_NUM_PREDICT` | Max generated tokens per reply | No | `192` |
| `OLLAMA_TEMPERATURE` | Response creativity level | No | `0.6` |
| `OLLAMA_TIMEOUT_SECONDS` | Ollama read timeout | No | `120` |
| `OLLAMA_KEEP_ALIVE` | Keep model loaded in memory | No | `30m` |
| `CHAT_HISTORY_MESSAGES` | Max history messages sent per request | No | `6` |
| `RAG_TOP_K` | Number of retrieved chunks per RAG query | No | `3` |
| `RAG_CHUNK_SIZE` | Characters per RAG chunk | No | `700` |
| `RAG_CHUNK_OVERLAP` | Character overlap between chunks | No | `120` |
| `WEB_LOOKUP_TOP_K` | Max Google result snippets to include | No | `5` |
| `GOOGLE_API_KEY` | Google Custom Search API key | For Web Mode | Empty |
| `GOOGLE_CSE_ID` | Google Custom Search Engine ID | For Web Mode | Empty |
| `FLASK_ENV` | Flask environment | No | `production` |
| `FLASK_DEBUG` | Enable Flask debug mode | No | `False` |
| `PORT` | Port to run the server | No | `5000` |
| `HOST` | Host to bind the server | No | `0.0.0.0` |
| `SECRET_KEY` | Flask secret key | No | Auto-generated |

### Available Ollama Models

You can change the model by updating the `OLLAMA_MODEL` environment variable:

- `llama3.1:8b` - **CURRENT & RECOMMENDED** (4.9GB, best balance of quality and performance)
- `llama3.2:3b` - Smaller, faster (2GB, good for limited RAM)
- `llama3.2:1b` - Smallest, fastest (1.3GB, basic quality)
- `llama2` - Original model (3.8GB, older version)
- `codellama` - Code-specialized model (7B, 4.1GB)

To switch models:
```bash
# Pull a different model
docker exec ollama-server ollama pull llama3.2:3b

# Update .env file
OLLAMA_MODEL=llama3.2:3b

# Restart chatbot
docker compose restart chatbot
```

## 🔒 Security

- Non-root container user for enhanced security
- Environment variables for sensitive data
- CORS configuration for API access control
- Health check endpoints for monitoring
- Trivy security scanning in CI/CD pipeline
- Resource limits in Kubernetes deployment

## 📊 CI/CD Pipeline

The GitHub Actions pipeline automatically:

1. **Lints** Python code with flake8 and black
2. **Builds** Docker image
3. **Tests** the container
4. **Scans** for security vulnerabilities with Trivy
5. **Uploads** security results to GitHub Security
6. **Notifies** deployment readiness

## 🎨 Architecture

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend (HTML │
│   CSS, JS)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Flask Backend   │
│ (Python 3.11)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Ollama Server   │
│ Llama 3.1 8B    │
└─────────────────┘
```

## 📝 Project Structure

```
ai-chatbot/
├── .github/
│   └── workflows/
│       └── ci-cd.yaml          # CI/CD pipeline
├── k8s/
│   ├── configmap.yaml          # Kubernetes ConfigMap
│   ├── deployment.yaml         # Kubernetes Deployment
│   ├── secret.yaml.example     # Secret template
│   └── service.yaml            # Kubernetes Service
├── static/
│   ├── index.html              # Frontend HTML
│   ├── style.css               # Styling
│   └── script.js               # Chat functionality
├── .dockerignore               # Docker ignore rules
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── app.py                      # Flask application
├── docker-compose.yml          # Docker Compose config
├── Dockerfile                  # Container image definition
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for providing free, local LLM inference
- [Meta AI](https://ai.meta.com/) for the Llama 3.1 model
- Flask framework and community
- Docker and Kubernetes communities
- Font Awesome for icons

## 📧 Contact

- **Email**: alexm051197@gmail.com
- **GitHub**: [@alexmachulsky](https://github.com/alexmachulsky)
- **LinkedIn**: [Alex Machulsky](https://www.linkedin.com/in/alex-machulsky-)

---

**Built with ❤️ by Alex Machulsky | DevOps Engineer**
