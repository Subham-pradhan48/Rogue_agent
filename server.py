from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import os
import sys
import io

from codebase_indexer import index_codebase
from rogue_agent import run_agent, run_django_agent, run_react_agent, run_fullstack_agent

app = FastAPI()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Request Models ───────────────────────────────────────────────────────────

class IndexRequest(BaseModel):
    project_dir: str

class RunRequest(BaseModel):
    project_dir: str
    main_script: str

class DjangoRunRequest(BaseModel):
    backend_dir: str
    main_script: str = "manage.py"

class ReactRunRequest(BaseModel):
    frontend_dir: str
    frontend_command: str = "build"

class FullstackRunRequest(BaseModel):
    backend_dir: str
    main_script: str = "manage.py"
    frontend_dir: str
    frontend_command: str = "build"

class FullstackIndexRequest(BaseModel):
    backend_dir: str
    frontend_dir: str


# ─── Streaming Helper ─────────────────────────────────────────────────────────

def make_stream(fn, *args):
    """Wraps a synchronous function call in a stdout-capturing async generator."""
    async def log_stream():
        old_stdout = sys.stdout
        sys.stdout = stream = io.StringIO()
        try:
            task = asyncio.create_task(asyncio.to_thread(fn, *args))
            last_pos = 0
            while not task.done():
                stream.seek(last_pos)
                new_output = stream.read()
                if new_output:
                    yield new_output
                    last_pos = stream.tell()
                yield " \n"
                await asyncio.sleep(0.5)

            stream.seek(last_pos)
            new_output = stream.read()
            if new_output:
                yield new_output
        except Exception as e:
            yield f"[Error] {str(e)}\n"
        finally:
            sys.stdout = old_stdout

    return log_stream()


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


# -- Single-app endpoints (original) --

@app.post("/api/index")
async def api_index(req: IndexRequest):
    return StreamingResponse(
        make_stream(index_codebase, req.project_dir),
        media_type="text/plain"
    )

@app.post("/api/run")
async def api_run(req: RunRequest):
    return StreamingResponse(
        make_stream(run_agent, req.project_dir, req.main_script),
        media_type="text/plain"
    )


# -- Django-only endpoint --

@app.post("/api/run-django")
async def api_run_django(req: DjangoRunRequest):
    return StreamingResponse(
        make_stream(run_django_agent, req.backend_dir, req.main_script),
        media_type="text/plain"
    )


# -- React-only endpoint --

@app.post("/api/run-react")
async def api_run_react(req: ReactRunRequest):
    return StreamingResponse(
        make_stream(run_react_agent, req.frontend_dir, req.frontend_command),
        media_type="text/plain"
    )


# -- Fullstack (Django + React) endpoints --

@app.post("/api/index-fullstack")
async def api_index_fullstack(req: FullstackIndexRequest):
    def index_both():
        print("=== Indexing Django Backend ===")
        index_codebase(req.backend_dir)
        print("\n=== Indexing React Frontend ===")
        index_codebase(req.frontend_dir)
        print("\n=== Indexing complete ===")

    return StreamingResponse(
        make_stream(index_both),
        media_type="text/plain"
    )

@app.post("/api/run-fullstack")
async def api_run_fullstack(req: FullstackRunRequest):
    return StreamingResponse(
        make_stream(
            run_fullstack_agent,
            req.backend_dir,
            req.main_script,
            req.frontend_dir,
            req.frontend_command,
        ),
        media_type="text/plain"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
