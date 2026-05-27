// ─────────────────────────────────────────────────────────────────────────────
// Rogue Agent Dashboard — script.js
// Handles mode switching, API calls, and terminal streaming output.
// ─────────────────────────────────────────────────────────────────────────────

'use strict';

// ── State ─────────────────────────────────────────────────────────────────────

let currentMode = 'single'; // 'single' | 'django' | 'react' | 'fullstack'

// ── Terminal ──────────────────────────────────────────────────────────────────

const terminal = document.getElementById('terminal');
const terminalTitle = document.getElementById('terminal-title');

/**
 * Appends a line to the terminal with the appropriate CSS class.
 * @param {string} message
 */
function appendLog(message) {
    const line = document.createElement('div');
    line.className = `log-line ${classifyLog(message)}`;
    line.textContent = message;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

/**
 * Determines the CSS class for a log line based on its content.
 * @param {string} text
 * @returns {string}
 */
function classifyLog(text) {
    if (text.includes('SUCCESS') || text.includes('succeeded') || text.includes('HEALED')) return 'success';
    if (text.includes('ERROR') || text.includes('CRASH') || text.includes('Failed') || text.includes('Error')) return 'error';
    if (text.includes('[Agent]') || text.includes('[Django Agent]') || text.includes('[React Agent]') || text.includes('[Fullstack Agent]')) return 'agent';
    if (text.includes('[Memory]') || text.includes('===')) return 'info';
    return 'system';
}

/** Clears all terminal output. */
function clearTerminal() {
    terminal.innerHTML = '<div class="log-line system">Terminal cleared. Ready.</div>';
}

// ── Mode Switching ────────────────────────────────────────────────────────────

/**
 * Activates a mode tab and shows the corresponding form.
 * @param {'single'|'django'|'react'|'fullstack'} mode
 */
function switchMode(mode) {
    currentMode = mode;

    // Update tab button states
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`mode-${mode}`).classList.add('active');

    // Show the matching form, hide the rest
    document.querySelectorAll('.mode-form').forEach(form => form.classList.add('hidden'));
    document.getElementById(`form-${mode}`).classList.remove('hidden');
}

// ── API Streaming ─────────────────────────────────────────────────────────────

/**
 * Streams a POST request to the given URL and writes each line to the terminal.
 * @param {string} url       - API endpoint
 * @param {object} payload   - Request body
 * @param {string} label     - Human-readable label for the terminal title
 */
async function streamRequest(url, payload, label) {
    terminalTitle.textContent = label;
    appendLog(`> Starting: ${label}...`);

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            appendLog(`[HTTP Error] ${response.status} ${response.statusText}`, 'error');
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        // Read streamed chunks and flush complete lines to the terminal
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Hold the last incomplete line in the buffer

            for (const line of lines) {
                if (line.trim()) appendLog(line);
            }
        }

        // Flush any remaining buffer content
        if (buffer.trim()) appendLog(buffer);
        appendLog('─── Task Complete ───');

    } catch (err) {
        appendLog(`[Network Error] ${err.message}`);
    }
}

// ── Button State Helpers ──────────────────────────────────────────────────────

/**
 * Disables a button and replaces its text with a spinner.
 * @param {HTMLButtonElement} btn
 * @param {string} loadingText
 */
function setButtonLoading(btn, loadingText) {
    btn.disabled = true;
    btn.querySelector('.btn-text').innerHTML = `<span class="spinner"></span> ${loadingText}`;
}

/**
 * Re-enables a button and restores its original text.
 * @param {HTMLButtonElement} btn
 * @param {string} originalText
 */
function resetButton(btn, originalText) {
    btn.disabled = false;
    btn.querySelector('.btn-text').textContent = originalText;
}

// ── Single App Mode ───────────────────────────────────────────────────────────

async function runSingleIndex() {
    const dir = document.getElementById('single-project-dir').value.trim();
    if (!dir) return appendLog('[Error] Please enter a Project Directory Path.');

    const btn = document.getElementById('btn-index-single');
    setButtonLoading(btn, 'Indexing...');
    await streamRequest('/api/index', { project_dir: dir }, 'Indexing Codebase');
    resetButton(btn, 'Index Codebase');
}

async function runSingleAgent() {
    const dir = document.getElementById('single-project-dir').value.trim();
    const script = document.getElementById('single-main-script').value.trim();
    if (!dir || !script) return appendLog('[Error] Please fill in both fields.');

    const btn = document.getElementById('btn-run-single');
    setButtonLoading(btn, 'Agent Running...');
    await streamRequest('/api/run', { project_dir: dir, main_script: script }, 'Single App Monitor');
    resetButton(btn, 'Run Agent Monitor');
}

// ── Django Only Mode ──────────────────────────────────────────────────────────

async function runDjangoIndex() {
    const dir = document.getElementById('django-backend-dir').value.trim();
    if (!dir) return appendLog('[Error] Please enter the Django Backend Directory.');

    const btn = document.getElementById('btn-index-django');
    setButtonLoading(btn, 'Indexing...');
    await streamRequest('/api/index', { project_dir: dir }, 'Indexing Django Backend');
    resetButton(btn, 'Index Backend');
}

async function runDjangoAgent() {
    const dir = document.getElementById('django-backend-dir').value.trim();
    const script = document.getElementById('django-main-script').value.trim() || 'manage.py';
    if (!dir) return appendLog('[Error] Please enter the Django Backend Directory.');

    const btn = document.getElementById('btn-run-django');
    setButtonLoading(btn, 'Checking...');
    await streamRequest('/api/run-django', { backend_dir: dir, main_script: script }, 'Django Backend Monitor');
    resetButton(btn, 'Run Django Monitor');
}

// ── React Only Mode ───────────────────────────────────────────────────────────

async function runReactIndex() {
    const dir = document.getElementById('react-frontend-dir').value.trim();
    if (!dir) return appendLog('[Error] Please enter the React Frontend Directory.');

    const btn = document.getElementById('btn-index-react');
    setButtonLoading(btn, 'Indexing...');
    await streamRequest('/api/index', { project_dir: dir }, 'Indexing React Frontend');
    resetButton(btn, 'Index Frontend');
}

async function runReactAgent() {
    const dir = document.getElementById('react-frontend-dir').value.trim();
    const cmd = document.getElementById('react-build-command').value;
    if (!dir) return appendLog('[Error] Please enter the React Frontend Directory.');

    const btn = document.getElementById('btn-run-react');
    setButtonLoading(btn, 'Building...');
    await streamRequest('/api/run-react', { frontend_dir: dir, frontend_command: cmd }, 'React Frontend Monitor');
    resetButton(btn, 'Run React Monitor');
}

// ── Fullstack Mode ────────────────────────────────────────────────────────────

async function runFullstackIndex() {
    const backendDir = document.getElementById('fs-backend-dir').value.trim();
    const frontendDir = document.getElementById('fs-frontend-dir').value.trim();
    if (!backendDir || !frontendDir) return appendLog('[Error] Please fill in both Backend and Frontend directories.');

    const btn = document.getElementById('btn-index-fullstack');
    setButtonLoading(btn, 'Indexing...');
    await streamRequest('/api/index-fullstack', { backend_dir: backendDir, frontend_dir: frontendDir }, 'Indexing Fullstack Project');
    resetButton(btn, 'Index Both');
}

async function runFullstackAgent() {
    const backendDir  = document.getElementById('fs-backend-dir').value.trim();
    const mainScript  = document.getElementById('fs-main-script').value.trim() || 'manage.py';
    const frontendDir = document.getElementById('fs-frontend-dir').value.trim();
    const buildCmd    = document.getElementById('fs-build-command').value;

    if (!backendDir || !frontendDir) return appendLog('[Error] Please fill in both Backend and Frontend directories.');

    const btn = document.getElementById('btn-run-fullstack');
    setButtonLoading(btn, 'Monitoring...');
    await streamRequest(
        '/api/run-fullstack',
        { backend_dir: backendDir, main_script: mainScript, frontend_dir: frontendDir, frontend_command: buildCmd },
        'Fullstack Monitor (Django + React)'
    );
    resetButton(btn, 'Run Fullstack Monitor');
}
