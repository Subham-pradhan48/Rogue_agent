# 🤖 Rogue Agent

> **An autonomous, self-healing AI agent that detects runtime crashes and build errors in your codebase — and fixes them automatically using a local LLM.**

---

## 📌 Overview

**Rogue Agent** is a local-first autonomous debugging assistant powered by [Ollama](https://ollama.com/) (Llama 3.2) and vector memory (ChromaDB). It monitors your Python, Django, and React projects, detects crashes or build failures, isolates the broken file, and applies an AI-generated patch — all without sending your code to any external server.

---

## ✨ Features

- 🐍 **Python Script Monitor** — Runs your Python script, captures crashes, and auto-patches the faulty file
- 🦄 **Django Backend Agent** — Runs `manage.py check` and heals Django configuration/code errors
- ⚛️ **React Frontend Agent** — Runs `npm run build`, parses JSX/TSX/JS build errors, and fixes them
- 🌐 **Fullstack Agent** — Chains Django + React monitoring in a single workflow
- 🧠 **Vector Memory (ChromaDB)** — Indexes your codebase so the agent can find the right file even when tracebacks are ambiguous
- 🔁 **Self-Verification Loop** — After patching, the agent re-runs the project to confirm the fix worked
- 🖥️ **Web UI + REST API** — FastAPI server with a browser-based dashboard for controlling the agent

---

## 🏗️ Architecture

```
rogue_agent_project/
├── rogue_agent.py        # Core agent logic (Python, Django, React, Fullstack)
├── codebase_indexer.py   # Crawls & indexes your codebase into ChromaDB
├── server.py             # FastAPI REST API + streaming logs server
├── requirements.txt      # Python dependencies
├── src/                  # Your target Python project goes here
│   ├── main.py
│   └── utils.py
├── static/               # Frontend UI served by FastAPI
│   └── index.html
└── agent_memory/         # ChromaDB vector store (auto-created)
```

---

## ⚙️ Prerequisites

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Runtime |
| [Ollama](https://ollama.com/) | Local LLM inference |
| Node.js + npm | Required only for React agent |

### Pull Required Ollama Models

```bash
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/Subham-pradhan48/Rogue_agent.git
cd Rogue_agent/rogue_agent_project

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🧪 Usage

### 1️⃣ Index Your Codebase (Recommended First Step)

Place your Python project files inside the `src/` directory, then index them into vector memory:

```bash
python codebase_indexer.py
```

---

### 2️⃣ Run the Agent (CLI Modes)

#### 🐍 Python Script Mode
```python
# In rogue_agent.py (bottom of file) or your own script:
from rogue_agent import run_agent
run_agent(project_dir="src", main_script="main.py")
```

#### 🦄 Django Backend Mode
```python
from rogue_agent import run_django_agent
run_django_agent(backend_dir="path/to/django_project")
```

#### ⚛️ React Frontend Mode
```python
from rogue_agent import run_react_agent
run_react_agent(frontend_dir="path/to/react_project", build_command="build")
```

#### 🌐 Fullstack Mode (Django + React)
```python
from rogue_agent import run_fullstack_agent
run_fullstack_agent(
    backend_dir="path/to/backend",
    main_script="manage.py",
    frontend_dir="path/to/frontend",
    frontend_command="build"
)
```

---

### 3️⃣ Run via Web UI (FastAPI Server)

```bash
python server.py
```

Then open your browser at: **http://127.0.0.1:8000**

#### Available API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the Web UI |
| `POST` | `/api/index` | Index a Python project |
| `POST` | `/api/run` | Run Python script agent |
| `POST` | `/api/run-django` | Run Django backend agent |
| `POST` | `/api/run-react` | Run React frontend agent |
| `POST` | `/api/index-fullstack` | Index both Django + React |
| `POST` | `/api/run-fullstack` | Run fullstack agent |

All endpoints return **streaming plain-text logs** in real time.

#### Example API Request

```bash
curl -X POST http://127.0.0.1:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{"project_dir": "src", "main_script": "main.py"}'
```

---

## 🔄 How It Works

```
1. Agent runs your project (subprocess)
         │
         ▼
2. Crash / Build Error detected?
   ├── YES ──► Parse traceback / build log for faulty file path
   │              │
   │              ├── Path found? ──► Read file
   │              └── Path NOT found? ──► Query ChromaDB vector memory
   │
   ▼
3. Send (file path + original code + crash log) to local Llama 3.2 LLM
         │
         ▼
4. LLM returns patched code (validated for syntax errors)
         │
         ▼
5. Write patch back to disk
         │
         ▼
6. Re-run project to verify fix
   ├── SUCCESS ──► "Codebase has self-healed ✅"
   └── FAILED  ──► "Next cascading error reported ❌"
```

---

## 📦 Dependencies

```
langchain-community
langchain-chroma
langchain-text-splitters
chromadb
langchain-ollama
fastapi
uvicorn
```

---

## 🔒 Privacy

All LLM inference runs **100% locally** via Ollama. Your source code is never sent to any external API or cloud service.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

This project is open-source. See [LICENSE](LICENSE) for details.

---

## 👤 Author

**Subham Pradhan**  
GitHub: [@Subham-pradhan48](https://github.com/Subham-pradhan48)
