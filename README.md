# Predictive Agentic AI Demo: RAG + CAG for Incident Management

## 🎯 Demo Overview

This demo showcases a Predictive Agentic AI system that combines:
- **RAG (Retrieval Augmented Generation)**: Retrieves relevant solutions from knowledge base
- **CAG (Corrective Augmented Generation)**: Self-corrects and improves responses
- **Predictive Analytics**: Forecasts incident severity and resolution time
- **Autonomous Agents**: Self-learning and decision-making capabilities

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Web Interface                        │
│                   (React Dashboard)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   API Gateway                            │
│                  (FastAPI + WebSocket)                   │
└──┬────────────┬────────────┬────────────┬──────────────┘
   │            │            │            │
┌──▼──┐    ┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│ RAG │    │  CAG  │    │Predict│    │ Agent │
│Engine│   │Engine │    │Engine │    │Manager│
└──┬──┘    └───┬───┘    └───┬───┘    └───┬───┘
   │           │            │            │
┌──▼───────────▼────────────▼────────────▼──┐
│          Core Services Layer               │
│  ┌─────────┐ ┌──────────┐ ┌────────────┐ │
│  │ChromaDB │ │  Ollama  │ │   Redis    │ │
│  │(Vectors)│ │  (LLM)   │ │(Events)    │ │
│  └─────────┘ └──────────┘ └────────────┘ │
└────────────────────────────────────────────┘
```

## 📋 Prerequisites

- Docker Desktop (with Docker Compose)
- 16GB RAM minimum (for running local LLM)
- 20GB free disk space
- Python 3.11+ (for development)
- Node.js 18+ (for frontend development)

## 🚀 Quick Start (5-Minute Setup)

### Step 1: Clone and Navigate
```bash
# Create project directory
mkdir agentic-ai-demo
cd agentic-ai-demo

# Copy all provided files to this directory
```

### Step 2: Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# No changes needed for local demo
```

### Step 3: Start All Services
```bash
# Build and start all containers
docker-compose up --build

# This will:
# 1. Download Ollama and Llama 3.2 model (~4GB)
# 2. Set up ChromaDB vector store
# 3. Load sample incident data
# 4. Start all services
```

### Step 4: Access the Demo
```
- Web Interface: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Monitoring Dashboard: http://localhost:3001
```

## 🎮 Demo Scenarios for Students

### Scenario 1: Basic RAG Demo
1. Submit a new incident: "Database connection timeout error"
2. Watch RAG engine retrieve similar past incidents
3. See recommended solutions ranked by relevance

### Scenario 2: CAG in Action
1. Submit incident with vague description
2. Observe initial RAG response
3. Watch CAG engine refine and correct the response
4. See confidence scores improve

### Scenario 3: Predictive Analytics
1. Submit high-priority incident
2. See predicted resolution time
3. Watch severity classification
4. Observe resource allocation suggestions

### Scenario 4: Agentic Behavior
1. Submit complex multi-system incident
2. Watch autonomous agent coordination
3. See decision tree visualization
4. Observe self-learning from feedback

## 📁 Project Structure

```
agentic-ai-demo/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── agents/              # Autonomous agents
│   │   │   ├── rag_agent.py     # RAG implementation
│   │   │   ├── cag_agent.py     # CAG implementation
│   │   │   └── predictor.py     # Predictive models
│   │   ├── services/            # Core services
│   │   ├── models/              # Data models
│   │   └── api/                 # API endpoints
│   ├── data/
│   │   ├── incidents.json       # Sample incidents
│   │   ├── knowledge_base.json  # Solution repository
│   │   └── embeddings/          # Pre-computed vectors
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Application pages
│   │   └── services/            # API clients
│   └── package.json
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── init-scripts/            # Database initialization
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔧 Configuration Options

### Adjusting Model Parameters
Edit `backend/config.yaml`:
```yaml
llm:
  model: "llama3.2:3b"  # Can use larger models if RAM permits
  temperature: 0.7
  max_tokens: 1024

rag:
  chunk_size: 512
  overlap: 50
  top_k: 5

cag:
  correction_threshold: 0.7
  max_iterations: 3
  confidence_target: 0.85
```

## 💡 Key Concepts Demonstrated

### RAG (Retrieval Augmented Generation)
- Vector similarity search
- Contextual embedding
- Dynamic knowledge retrieval
- Relevance scoring

### CAG (Corrective Augmented Generation)
- Self-reflection mechanisms
- Iterative refinement
- Confidence scoring
- Feedback integration

### Agentic AI Features
- Autonomous decision-making
- Multi-agent coordination
- Goal-oriented behavior
- Continuous learning

## 📊 Monitoring & Metrics

Access monitoring dashboard at http://localhost:3001 to see:
- Response accuracy metrics
- Processing latency
- Agent coordination visualizations
- Learning curve graphs

## 🧪 Testing the System

### Load Testing
```bash
# Run performance tests
docker exec backend python tests/load_test.py

# This simulates 100 concurrent incidents
```

### Accuracy Testing
```bash
# Test RAG accuracy
docker exec backend python tests/test_rag_accuracy.py

# Test CAG improvements
docker exec backend python tests/test_cag_effectiveness.py
```

## 🎓 Educational Resources

### For Instructors
- Slide deck available in `/presentations`
- Lab exercises in `/labs`
- Assessment rubrics in `/assessments`

### For Students
- Interactive tutorials at http://localhost:3000/tutorial
- API playground at http://localhost:8000/docs
- Code walkthroughs in `/documentation`

## 🐛 Troubleshooting

### Common Issues

1. **Ollama model download fails**
   ```bash
   docker exec ollama ollama pull llama3.2:3b
   ```

2. **Out of memory errors**
   - Reduce model size in config
   - Decrease batch size
   - Limit concurrent requests

3. **ChromaDB connection issues**
   ```bash
   docker-compose restart chromadb
   ```

## 📚 Further Reading

- [RAG Paper](https://arxiv.org/abs/2005.11401)
- [CAG Concepts](https://arxiv.org/abs/2401.15884)
- [Agentic AI Patterns]

## 🤝 Support

For demo issues or questions:
- Check `/documentation/FAQ.md`
- Review logs: `docker-compose logs -f`
- Debug mode: Set `DEBUG=true` in `.env`

## 📄 License

MIT License - Feel free to use for educational purposes

---