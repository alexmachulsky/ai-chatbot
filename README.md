# DevOps ChatBot 🤖

An AI-powered chatbot application designed to assist with DevOps tasks, questions, and best practices. Built with Python Flask, Ollama (local LLM), Docker, and Kubernetes.

![DevOps ChatBot](https://img.shields.io/badge/DevOps-ChatBot-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue)

## 🌟 Features

- **AI-Powered Responses**: Uses Ollama with Llama 3.1 8B for intelligent DevOps assistance (100% free, runs locally)
- **Modern UI**: Clean, responsive chat interface with smooth animations and glassmorphism effects
- **Conversation History**: Maintains context across multiple messages
- **DevOps Expertise**: Specialized in Docker, Kubernetes, CI/CD, Terraform, Ansible, and more
- **Production Ready**: Containerized with Docker and deployable to Kubernetes
- **Health Checks**: Built-in health endpoints for monitoring
- **Security**: Non-root container user, environment variable management
- **No API Keys**: Runs completely locally with Ollama - no external API dependencies
- **High Quality Responses**: 8B parameter model provides detailed explanations with code examples

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
   git clone https://github.com/alexmachulsky/devops-chatbot.git
   cd devops-chatbot
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

### Docker Deployment

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

### Kubernetes Deployment

> **Note**: Kubernetes deployment requires updating the manifests to include Ollama service. Currently optimized for Docker Compose deployment.

1. **Create ConfigMap**:
   ```bash
   cd k8s
   kubectl apply -f configmap.yaml
   ```

2. **Deploy the application**:
   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   ```

3. **Check deployment status**:
   ```bash
   kubectl get pods -l app=devops-chatbot
   kubectl get svc devops-chatbot
   ```

4. **Access the application**:
   ```bash
   # If using LoadBalancer
   kubectl get svc devops-chatbot
   
   # If using port-forward
   kubectl port-forward svc/devops-chatbot 5000:80
   ```

## 📋 API Endpoints

### POST /api/chat
Send a message to the chatbot.

**Request**:
```json
{
  "message": "How do I create a Dockerfile?",
  "history": []
}
```

**Response**:
```json
{
  "message": "To create a Dockerfile...",
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

The DevOps ChatBot can help with:

- **Docker**: Container creation, optimization, troubleshooting
- **Kubernetes**: Resource management, deployments, debugging
- **CI/CD**: Pipeline setup, GitHub Actions, Jenkins
- **Infrastructure as Code**: Terraform modules, Ansible playbooks
- **Cloud Platforms**: AWS, Azure, GCP best practices
- **Monitoring**: Prometheus, Grafana, ELK/EFK stack
- **Security**: Best practices, vulnerability scanning
- **Troubleshooting**: Common DevOps issues and solutions

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OLLAMA_URL` | Ollama server URL | No | `http://ollama:11434` |
| `OLLAMA_MODEL` | Ollama model to use | No | `llama3.2:1b` |
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
│  OpenAI API     │
│  GPT-3.5-turbo  │
└─────────────────┘
```

## 📝 Project Structure

```
devops-chatbot/
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

- OpenAI for the GPT-3.5 API
- Flask framework and community
- Docker and Kubernetes communities

## 📧 Contact

- **Email**: alexm051197@gmail.com
- **GitHub**: [@alexmachulsky](https://github.com/alexmachulsky)
- **LinkedIn**: [Alex Machulsky](https://www.linkedin.com/in/alex-machulsky-)

---

**Built with ❤️ by Alex Machulsky | DevOps Engineer**
