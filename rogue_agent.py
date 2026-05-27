import subprocess
import os
import re
import ast
from typing import Optional

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM


# ─── Utilities ──────────────────────────────────────────────────────────────

def get_npm_cmd() -> str:
    """Returns the correct npm command for the current OS."""
    return "npm.cmd" if os.name == "nt" else "npm"


# ─── Python / Django Helpers ─────────────────────────────────────────────────

def parse_crash_file(stderr_log: str, project_dir: str) -> Optional[str]:
    """Finds the precise file path from a standard Python crash log."""
    matches = re.findall(r'File "([^"]+\.py)"', stderr_log)
    if matches:
        return os.path.abspath(os.path.join(project_dir, matches[-1]))
    return None


def find_file_via_vector_search(crash_log: str, persist_dir: str = "./agent_memory") -> Optional[str]:
    """Queries vector memory to find the most relevant file when path parsing fails."""
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    matched_docs = vector_store.similarity_search(crash_log, k=1)
    if matched_docs:
        return matched_docs[0].metadata.get("source_file_path")
    return None


def generate_patch(target_file: str, original_code: str, crash_log: str) -> str:
    """Uses the local LLM to generate a clean, executable Python patch."""
    llm = OllamaLLM(model="llama3.2:1b", temperature=0.0)

    prompt = f"""
    You are an autonomous senior QA developer. A Python file in a multi-file system crashed.

    FILE PATH: {target_file}

    ORIGINAL CODE:
    {original_code}

    CRASH LOG DETECTED:
    {crash_log}

    Task: Fix the bug causing the crash. Return the ENTIRE updated file source code.
    If there is a division by zero or similar math error, return a safe fallback value (like 0) instead of raising an exception.
    Keep all original function structures and imports exactly intact so you don't break other files.
    You MUST wrap your response in ```python and ``` tags. Do not output any other text or explanations.
    """

    raw_patch = llm.invoke(prompt)

    match = re.search(r"```(?:python)?(.*?)```", raw_patch, re.DOTALL | re.IGNORECASE)
    code = match.group(1).strip() if match else raw_patch.strip()
    code = code.replace("```python", "").replace("```", "")

    lines = code.split("\n")
    while lines:
        try:
            ast.parse("\n".join(lines))
            return "\n".join(lines)
        except SyntaxError:
            lines.pop()

    return code


# ─── React / Node.js Helpers ─────────────────────────────────────────────────

def parse_react_error_file(build_output: str, frontend_dir: str) -> Optional[str]:
    """Extracts the file path from a React/Webpack/Vite build error output."""
    patterns = [
        r"([^\s]+\.(?:jsx?|tsx?))\s*:\s*\d+:\d+",          # file.jsx:10:5
        r"(?:ERROR in |error in )([^\s]+\.(?:jsx?|tsx?))",   # ERROR in src/App.jsx
        r"(?:src/|\.\/src/)([^\s:]+\.(?:jsx?|tsx?))",        # src/App.jsx
    ]
    for pattern in patterns:
        matches = re.findall(pattern, build_output)
        if matches:
            raw = matches[0]
            # Ensure it starts with src/ for relative resolution
            if not raw.startswith(("src/", "./src/", "/")):
                raw = f"src/{raw}"
            full_path = os.path.abspath(os.path.join(frontend_dir, raw))
            if os.path.exists(full_path):
                return full_path
    return None


def generate_js_patch(target_file: str, original_code: str, error_log: str) -> str:
    """Uses the local LLM to generate a clean JS/JSX/TSX patch."""
    llm = OllamaLLM(model="llama3.2:1b", temperature=0.0)

    ext = os.path.splitext(target_file)[1].lower()
    lang = "TypeScript" if ext in (".ts", ".tsx") else "JavaScript"
    framework = "React JSX/TSX" if ext in (".jsx", ".tsx") else lang

    prompt = f"""
    You are an autonomous senior frontend developer. A {framework} file has a build error.

    FILE PATH: {target_file}

    ORIGINAL CODE:
    {original_code}

    BUILD ERROR:
    {error_log}

    Task: Fix the bug causing the build error. Return the ENTIRE updated file source code.
    Keep all original component structures and imports exactly intact.
    You MUST wrap your response in ```javascript and ``` tags. Do not output any other text or explanations.
    """

    raw_patch = llm.invoke(prompt)
    match = re.search(
        r"```(?:javascript|jsx|typescript|tsx|js|ts)?(.*?)```",
        raw_patch,
        re.DOTALL | re.IGNORECASE,
    )
    code = match.group(1).strip() if match else raw_patch.strip()
    return code


# ─── Single-App Agent (original behaviour) ───────────────────────────────────

def run_agent(project_dir: str = "src", main_script: str = "main.py") -> None:
    """Main agent loop that monitors execution, handles errors, and patches bugs."""
    print("[Agent] Initiating runtime subprocess monitor...")

    result = subprocess.run(
        ["python", main_script], cwd=project_dir, capture_output=True, text=True
    )

    if result.returncode == 0:
        print("[Agent] Clean execution. No bugs found.")
        return

    crash_log = result.stderr
    print(f"\n[Agent] CRASH DETECTED!\n--- TRACEBACK ---\n{crash_log}-----------------")

    target_file = parse_crash_file(crash_log, project_dir)

    if not target_file or not os.path.exists(target_file):
        print("[Agent] Traceback path parsing failed. Querying vector memory...")
        target_file = find_file_via_vector_search(crash_log)

        if not target_file or not os.path.exists(target_file):
            print("[Agent] Critical Error: Target code block is untraceable.")
            return

    print(f"[Agent] Isolated target file: {target_file}")

    with open(target_file, "r", encoding="utf-8") as f:
        original_code = f.read()

    print("[Agent] Requesting local patch layout from Llama3...")
    clean_code = generate_patch(target_file, original_code, crash_log)

    print("\n[Agent] PROPOSED SOLUTION:")
    print("-" * 40)
    print(clean_code)
    print("-" * 40)

    print(f"\n[Agent] Patching code changes directly into {target_file}...")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(clean_code)

    print("[Agent] Verifying integrity via automated integration check...")
    retry_result = subprocess.run(
        ["python", main_script], cwd=project_dir, capture_output=True, text=True
    )

    if retry_result.returncode == 0:
        print("\n[Agent] SUCCESS! The codebase has self-healed and executes cleanly.")
    else:
        print(f"\n[Agent] Patch failed. Next cascading trace encountered:\n{retry_result.stderr}")


# ─── Django Backend Agent ─────────────────────────────────────────────────────

def run_django_agent(backend_dir: str, main_script: str = "manage.py") -> None:
    """Monitors a Django backend using `manage.py check` and auto-patches Python errors."""
    print(f"[Django Agent] Running system check: python {main_script} check")
    print(f"[Django Agent] Backend directory: {backend_dir}")

    result = subprocess.run(
        ["python", main_script, "check"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )

    combined = result.stdout + "\n" + result.stderr

    if result.returncode == 0:
        print("[Django Agent] System check passed. No Django errors found.")
        return

    print(f"\n[Django Agent] ERROR DETECTED!\n--- CHECK LOG ---\n{combined}\n-----------------")

    target_file = parse_crash_file(combined, backend_dir)

    if not target_file or not os.path.exists(target_file):
        print("[Django Agent] Standard path parsing failed. Querying vector memory...")
        target_file = find_file_via_vector_search(combined)

        if not target_file or not os.path.exists(target_file):
            print("[Django Agent] Critical Error: Could not isolate the faulty file.")
            return

    print(f"[Django Agent] Isolated target file: {target_file}")

    with open(target_file, "r", encoding="utf-8") as f:
        original_code = f.read()

    print("[Django Agent] Requesting patch from local LLM...")
    clean_code = generate_patch(target_file, original_code, combined)

    print("\n[Django Agent] PROPOSED SOLUTION:")
    print("-" * 40)
    print(clean_code)
    print("-" * 40)

    print(f"\n[Django Agent] Patching {target_file}...")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(clean_code)

    print("[Django Agent] Verifying fix...")
    retry = subprocess.run(
        ["python", main_script, "check"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )

    if retry.returncode == 0:
        print("\n[Django Agent] SUCCESS! Django backend passes all system checks.")
    else:
        print(
            f"\n[Django Agent] Patch failed. Still broken:\n{retry.stdout}\n{retry.stderr}"
        )


# ─── React Frontend Agent ─────────────────────────────────────────────────────

def run_react_agent(frontend_dir: str, build_command: str = "build") -> None:
    """Monitors a React frontend via `npm run <build_command>` and auto-patches JS/JSX/TSX files."""
    npm = get_npm_cmd()
    print(f"[React Agent] Running: npm run {build_command}")
    print(f"[React Agent] Frontend directory: {frontend_dir}")

    result = subprocess.run(
        [npm, "run", build_command],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
    )

    # React/Webpack build errors often appear in stdout
    combined = result.stdout + "\n" + result.stderr

    if result.returncode == 0:
        print("[React Agent] Build succeeded. No frontend errors found.")
        return

    print(f"\n[React Agent] BUILD ERROR DETECTED!\n--- BUILD LOG ---\n{combined}\n-----------------")

    target_file = parse_react_error_file(combined, frontend_dir)

    if not target_file or not os.path.exists(target_file):
        print("[React Agent] Could not isolate the error file from build output.")
        return

    print(f"[React Agent] Isolated target file: {target_file}")

    with open(target_file, "r", encoding="utf-8") as f:
        original_code = f.read()

    print("[React Agent] Requesting patch from local LLM...")
    clean_code = generate_js_patch(target_file, original_code, combined)

    print("\n[React Agent] PROPOSED SOLUTION:")
    print("-" * 40)
    print(clean_code)
    print("-" * 40)

    print(f"\n[React Agent] Patching {target_file}...")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(clean_code)

    print("[React Agent] Verifying fix with another build...")
    retry = subprocess.run(
        [npm, "run", build_command],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
    )

    if retry.returncode == 0:
        print("\n[React Agent] SUCCESS! React frontend builds cleanly.")
    else:
        print(
            f"\n[React Agent] Patch failed. Build still broken:\n{retry.stdout}\n{retry.stderr}"
        )


# ─── Fullstack Agent (Django + React) ────────────────────────────────────────

def run_fullstack_agent(
    backend_dir: str,
    main_script: str,
    frontend_dir: str,
    frontend_command: str = "build",
) -> None:
    """Runs Django backend agent first, then React frontend agent."""
    print("=" * 55)
    print("[Fullstack Agent] Starting Backend (Django) Monitor...")
    print("=" * 55)
    run_django_agent(backend_dir, main_script)

    print("\n" + "=" * 55)
    print("[Fullstack Agent] Starting Frontend (React) Monitor...")
    print("=" * 55)
    run_react_agent(frontend_dir, frontend_command)

    print("\n" + "=" * 55)
    print("[Fullstack Agent] Fullstack monitoring complete.")
    print("=" * 55)


if __name__ == "__main__":
    run_agent()
