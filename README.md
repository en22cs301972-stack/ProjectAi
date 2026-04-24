# AI-Powered Learning Platform with Agent System

A comprehensive full-stack AI-powered platform combining interactive coding education, structured courses, an AI tutor, and autonomous AI agents.

## 🚀 Features

### 1. Learning Module
- **Interactive Code Editor** - Supports Python, Java, and SQL with syntax highlighting via CodeMirror
- **Real-time Code Execution** - Run code in a sandboxed environment with stdin support
- **AI-powered Debug** - Line-by-line error explanation using GPT-4o
- **Fix Suggestions** - AI suggests exact code changes with locations
- **Test Cases** - Auto-validate code against test cases

### 2. Course System
- **Structured Courses** - Beginner to Advanced levels for Python, Java, and SQL
- **Progress Tracking** - Per-lesson progress with percentage completion
- **Auto-generate Certificates** - PDF certificates issued upon course completion

### 3. AI Tutor
- **Chat Interface** - Ask any programming question
- **Code Context** - Paste code for context-aware responses
- **Hinglish Support** - Responses in English or Hinglish (Hindi + English mix)
- **Session History** - Persistent chat sessions

### 4. Agent System (Core Feature)
- **Custom AI Agents** - Create agents with your own API keys
- **Gmail Integration** - Read, reply to emails automatically
- **Market/Crypto APIs** - Stock quotes and crypto prices
- **MCP Protocol** - Model Context Protocol for tool discovery
- **Start/Stop Controls** - Full agent lifecycle management
- **Multi-agent Support** - Run multiple agents simultaneously

### 5. Security
- **JWT Authentication** - Secure token-based auth
- **Google OAuth** - Sign in with Google (includes Gmail scope)
- **Encrypted API Keys** - Fernet encryption for sensitive keys
- **CORS Protection** - Configurable origins

## 📁 Project Structure

```
ProjectAi/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/routes/         # REST API endpoints
│   │   │   ├── auth.py         # Authentication & OAuth
│   │   │   ├── learning.py     # Code execution & debugging
│   │   │   ├── courses.py      # Course management
│   │   │   ├── tutor.py        # AI Tutor chat
│   │   │   └── agents.py       # Agent management
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   │   ├── code_execution.py  # Sandboxed code runner
│   │   │   ├── ai_service.py      # OpenAI integration
│   │   │   ├── certificate_service.py  # PDF generation
│   │   │   ├── mcp_service.py     # MCP tool management
│   │   │   └── gmail_agent.py     # Gmail auto-responder
│   │   ├── core/               # Security, Redis
│   │   ├── config.py           # Settings
│   │   ├── database.py         # Async PostgreSQL
│   │   └── main.py             # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React + Vite + Tailwind
│   ├── src/
│   │   ├── pages/              # Route pages
│   │   │   ├── Dashboard.jsx   # Stats & overview
│   │   │   ├── LearningPage.jsx # Code editor
│   │   │   ├── CoursesPage.jsx  # Course catalog
│   │   │   ├── TutorPage.jsx    # AI chat
│   │   │   └── AgentsPage.jsx   # Agent control panel
│   │   ├── components/layout/  # Sidebar, Navbar
│   │   ├── services/api.js     # Axios API client
│   │   └── store/authStore.js  # Zustand auth store
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml          # Full stack deployment
├── .env.example                # Environment template
└── README.md
```

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, CodeMirror 6 |
| Backend | FastAPI, Python 3.11, Pydantic v2 |
| Database | PostgreSQL 15 (async with asyncpg) |
| Cache | Redis 7 |
| AI | OpenAI GPT-4o, Anthropic Claude |
| Auth | JWT + Google OAuth 2.0 |
| Agent Tools | MCP (Model Context Protocol) |
| Deployment | Docker, Docker Compose |

## 🏃 Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone and configure
git clone https://github.com/en22cs301972-stack/ProjectAi.git
cd ProjectAi

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 3. Start everything
docker-compose up --build

# 4. Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your settings

# Start PostgreSQL and Redis (or use Docker)
docker-compose up postgres redis -d

uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for AI features |
| `SECRET_KEY` | JWT secret (use a long random string) |
| `ENCRYPTION_KEY` | Fernet key for API key encryption (32 bytes) |

### Optional Variables
| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | For Gmail OAuth integration |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret |
| `ANTHROPIC_API_KEY` | Alternative AI provider |

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | User registration |
| `POST /api/auth/login` | Login (returns JWT) |
| `POST /api/learning/execute` | Execute code |
| `POST /api/learning/debug` | AI debug code |
| `GET /api/courses` | List courses |
| `POST /api/courses/{id}/enroll` | Enroll in course |
| `POST /api/tutor/chat` | Chat with AI tutor |
| `GET /api/agents` | List agents |
| `POST /api/agents` | Create agent |
| `POST /api/agents/{id}/start` | Start agent |
| `GET /api/agents/tools/available` | List MCP tools |

Full API docs available at `http://localhost:8000/docs`

## 🤖 Creating a Gmail Auto-Responder Agent

1. Set up Google OAuth credentials in Google Cloud Console
2. Navigate to **AI Agents** → **New Agent**
3. Select type: `gmail`
4. Add your Gmail OAuth credentials as JSON
5. Enable the `gmail` tool
6. Click **Start** with task: "Auto-reply to unread emails"

## 🎓 Certificate Generation

Certificates are automatically generated as PDFs when a user completes 100% of a course. Download from the Profile page or via API.

## 🔐 Security Features

- Passwords hashed with bcrypt
- JWT tokens with configurable expiry
- API keys encrypted using Fernet (AES-128-CBC)
- CORS configured for frontend origins only

## 📄 License

MIT License