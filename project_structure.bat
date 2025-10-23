@echo off
REM Batch script to create agentic-ai-demo project structure
REM Run this script in Windows Terminal with: create_project_structure.bat

echo Creating agentic-ai-demo project structure...

REM Create main project directory
set PROJECT_ROOT=agentic-ai-demo
mkdir "%PROJECT_ROOT%" 2>nul

REM Backend structure
echo Creating backend structure...
mkdir "%PROJECT_ROOT%\backend\app\agents" 2>nul
mkdir "%PROJECT_ROOT%\backend\app\services" 2>nul
mkdir "%PROJECT_ROOT%\backend\app\models" 2>nul
mkdir "%PROJECT_ROOT%\backend\app\api" 2>nul
mkdir "%PROJECT_ROOT%\backend\data\embeddings" 2>nul

REM Create main.py
(
echo from fastapi import FastAPI
echo from fastapi.middleware.cors import CORSMiddleware
echo.
echo app = FastAPI^(title="Agentic AI Demo API"^)
echo.
echo # Configure CORS
echo app.add_middleware^(
echo     CORSMiddleware,
echo     allow_origins=["*"],
echo     allow_methods=["*"],
echo     allow_headers=["*"],
echo ^)
echo.
echo @app.get^("/")
echo def read_root^(^):
echo     return {"message": "Agentic AI Demo API"}
echo.
echo @app.get^("/health"^)
echo def health_check^(^):
echo     return {"status": "healthy"}
) > "%PROJECT_ROOT%\backend\app\main.py"

REM Create rag_agent.py
(
echo """
echo RAG ^(Retrieval Augmented Generation^) Agent Implementation
echo """
echo.
echo class RAGAgent:
echo     def __init__^(self^):
echo         self.knowledge_base = []
echo.        
echo     def retrieve^(self, query^):
echo         # Implement retrieval logic
echo         pass
echo.    
echo     def generate^(self, context, query^):
echo         # Implement generation logic
echo         pass
echo.    
echo     def answer^(self, query^):
echo         context = self.retrieve^(query^)
echo         response = self.generate^(context, query^)
echo         return response
) > "%PROJECT_ROOT%\backend\app\agents\rag_agent.py"

REM Create cag_agent.py
(
echo """
echo CAG ^(Corrective Augmented Generation^) Agent Implementation
echo """
echo.
echo class CAGAgent:
echo     def __init__^(self^):
echo         self.corrective_model = None
echo.        
echo     def correct^(self, response^):
echo         # Implement correction logic
echo         pass
echo.    
echo     def generate^(self, query^):
echo         # Implement generation with correction
echo         pass
) > "%PROJECT_ROOT%\backend\app\agents\cag_agent.py"

REM Create predictor.py
(
echo """
echo Predictive Models for incident prediction
echo """
echo.
echo class IncidentPredictor:
echo     def __init__^(self^):
echo         self.model = None
echo.        
echo     def train^(self, data^):
echo         # Implement training logic
echo         pass
echo.    
echo     def predict^(self, features^):
echo         # Implement prediction logic
echo         pass
) > "%PROJECT_ROOT%\backend\app\agents\predictor.py"

REM Create empty __init__.py files
type nul > "%PROJECT_ROOT%\backend\app\agents\__init__.py"
type nul > "%PROJECT_ROOT%\backend\app\services\__init__.py"
type nul > "%PROJECT_ROOT%\backend\app\models\__init__.py"
type nul > "%PROJECT_ROOT%\backend\app\api\__init__.py"

REM Create incidents.json
(
echo [
echo     {
echo         "id": 1,
echo         "title": "Database Connection Timeout",
echo         "description": "Application unable to connect to production database",
echo         "severity": "high",
echo         "status": "resolved",
echo         "solution": "Increased connection pool size and optimized query performance"
echo     },
echo     {
echo         "id": 2,
echo         "title": "Memory Leak in Service",
echo         "description": "Gradual memory increase in microservice causing crashes",
echo         "severity": "critical",
echo         "status": "resolved",
echo         "solution": "Fixed resource cleanup in background workers"
echo     }
echo ]
) > "%PROJECT_ROOT%\backend\data\incidents.json"

REM Create knowledge_base.json
(
echo {
echo     "solutions": [
echo         {
echo             "problem": "database timeout",
echo             "keywords": ["connection", "timeout", "database", "pool"],
echo             "solution": "Check connection pool settings, verify network connectivity, optimize queries",
echo             "tags": ["database", "performance"]
echo         },
echo         {
echo             "problem": "memory leak",
echo             "keywords": ["memory", "leak", "crash", "oom"],
echo             "solution": "Profile memory usage, check for unclosed resources, implement proper cleanup",
echo             "tags": ["memory", "performance", "debugging"]
echo         }
echo     ]
echo }
) > "%PROJECT_ROOT%\backend\data\knowledge_base.json"

REM Create requirements.txt
(
echo fastapi==0.104.1
echo uvicorn==0.24.0
echo pydantic==2.4.2
echo python-dotenv==1.0.0
echo numpy==1.24.3
echo pandas==2.1.3
echo scikit-learn==1.3.2
echo transformers==4.35.0
echo torch==2.1.0
echo langchain==0.0.335
echo chromadb==0.4.17
echo openai==1.3.0
echo httpx==0.25.1
) > "%PROJECT_ROOT%\backend\requirements.txt"

REM Frontend structure
echo Creating frontend structure...
mkdir "%PROJECT_ROOT%\frontend\src\components" 2>nul
mkdir "%PROJECT_ROOT%\frontend\src\pages" 2>nul
mkdir "%PROJECT_ROOT%\frontend\src\services" 2>nul

REM Create package.json
(
echo {
echo   "name": "agentic-ai-demo-frontend",
echo   "version": "0.1.0",
echo   "private": true,
echo   "dependencies": {
echo     "react": "^^18.2.0",
echo     "react-dom": "^^18.2.0",
echo     "react-router-dom": "^^6.18.0",
echo     "axios": "^^1.6.0",
echo     "chart.js": "^^4.4.0",
echo     "react-chartjs-2": "^^5.2.0",
echo     "@mui/material": "^^5.14.17",
echo     "@emotion/react": "^^11.11.1",
echo     "@emotion/styled": "^^11.11.0",
echo     "web-vitals": "^^3.5.0"
echo   },
echo   "scripts": {
echo     "start": "react-scripts start",
echo     "build": "react-scripts build",
echo     "test": "react-scripts test",
echo     "eject": "react-scripts eject"
echo   },
echo   "devDependencies": {
echo     "react-scripts": "5.0.1",
echo     "@types/react": "^^18.2.37",
echo     "@types/react-dom": "^^18.2.15",
echo     "typescript": "^^5.2.2"
echo   },
echo   "browserslist": {
echo     "production": [
echo       "^>0.2%%",
echo       "not dead",
echo       "not op_mini all"
echo     ],
echo     "development": [
echo       "last 1 chrome version",
echo       "last 1 firefox version",
echo       "last 1 safari version"
echo     ]
echo   }
echo }
) > "%PROJECT_ROOT%\frontend\package.json"

REM Docker structure
echo Creating Docker configuration...
mkdir "%PROJECT_ROOT%\docker\init-scripts" 2>nul

REM Create Dockerfile.backend
(
echo FROM python:3.11-slim
echo.
echo WORKDIR /app
echo.
echo COPY backend/requirements.txt .
echo RUN pip install --no-cache-dir -r requirements.txt
echo.
echo COPY backend/ .
echo.
echo ENV PYTHONUNBUFFERED=1
echo.
echo CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
) > "%PROJECT_ROOT%\docker\Dockerfile.backend"

REM Create Dockerfile.frontend
(
echo FROM node:18-alpine
echo.
echo WORKDIR /app
echo.
echo COPY frontend/package.json frontend/package-lock.json* ./
echo RUN npm ci
echo.
echo COPY frontend/ .
echo.
echo EXPOSE 3000
echo.
echo CMD ["npm", "start"]
) > "%PROJECT_ROOT%\docker\Dockerfile.frontend"

REM Create docker-compose.yml
(
echo version: '3.8'
echo.
echo services:
echo   backend:
echo     build:
echo       context: .
echo       dockerfile: docker/Dockerfile.backend
echo     ports:
echo       - "8000:8000"
echo     environment:
echo       - DATABASE_URL=postgresql://user:password@db:5432/agenticai
echo       - REDIS_URL=redis://redis:6379
echo     volumes:
echo       - ./backend:/app
echo     depends_on:
echo       - db
echo       - redis
echo.
echo   frontend:
echo     build:
echo       context: .
echo       dockerfile: docker/Dockerfile.frontend
echo     ports:
echo       - "3000:3000"
echo     environment:
echo       - REACT_APP_API_URL=http://localhost:8000
echo     volumes:
echo       - ./frontend:/app
echo       - /app/node_modules
echo     depends_on:
echo       - backend
echo.
echo   db:
echo     image: postgres:15
echo     environment:
echo       - POSTGRES_DB=agenticai
echo       - POSTGRES_USER=user
echo       - POSTGRES_PASSWORD=password
echo     volumes:
echo       - postgres_data:/var/lib/postgresql/data
echo       - ./docker/init-scripts:/docker-entrypoint-initdb.d
echo     ports:
echo       - "5432:5432"
echo.
echo   redis:
echo     image: redis:7-alpine
echo     ports:
echo       - "6379:6379"
echo.
echo volumes:
echo   postgres_data:
) > "%PROJECT_ROOT%\docker-compose.yml"

REM Create .env.example
(
echo # Backend Configuration
echo DATABASE_URL=postgresql://user:password@localhost:5432/agenticai
echo REDIS_URL=redis://localhost:6379
echo SECRET_KEY=your-secret-key-here
echo.
echo # AI/ML Configuration
echo OPENAI_API_KEY=your-openai-api-key
echo HUGGINGFACE_API_KEY=your-huggingface-api-key
echo.
echo # Frontend Configuration
echo REACT_APP_API_URL=http://localhost:8000
echo.
echo # Service Ports
echo BACKEND_PORT=8000
echo FRONTEND_PORT=3000
) > "%PROJECT_ROOT%\.env.example"

REM Create README.md
(
echo # Agentic AI Demo
echo.
echo A demonstration of autonomous AI agents for incident management and predictive analytics.
echo.
echo ## Quick Start
echo.
echo 1. Copy environment variables: cp .env.example .env
echo 2. Update .env with your API keys
echo 3. Start with Docker: docker-compose up
echo.
echo ## License
echo.
echo MIT License
) > "%PROJECT_ROOT%\README.md"

echo.
echo Project structure created successfully!
echo Location: %PROJECT_ROOT%
echo.
echo Next steps:
echo 1. Navigate to project: cd %PROJECT_ROOT%
echo 2. Configure environment: copy .env.example .env
echo 3. Start with Docker: docker-compose up
echo.
pause