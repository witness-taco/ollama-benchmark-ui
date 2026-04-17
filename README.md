# ollama-benchmark-ui
<img width="1192" height="921" alt="image" src="https://github.com/user-attachments/assets/e7fa8fe3-48bb-4cf1-bffa-874b7cd214e2" />

The landscape of local open-weight models moves incredibly fast. Testing them side-by-side usually involves juggling terminal windows or using heavy UI clients that try to load multiple models at once and crash your VRAM. 

This is a lightweight, gimmick-free web UI built specifically for **Ollama**. It allows you to select multiple local models, feed them a single prompt, and execute them strictly sequentially. 

It is designed to run quietly on a local server or homelab, forcefully managing VRAM so you can benchmark large models on constrained hardware without hanging.

## Features

- **Sequential Execution:** Queues models one by one to prevent Out-Of-Memory (OOM) errors.
- **Aggressive VRAM Management:** Injects `keep_alive: 0` into API calls to instantly unload models after generation. Includes a manual "Flush VRAM" panic button.
- **Live Streaming:** Uses Server-Sent Events (SSE) to stream tokens in real-time to the UI.
- **Markdown Export:** 1-click export of individual or collective benchmark results (including the prompt, outputs, and execution times) to `.md` files.
- **Minimalist Stack:** Just a Python/FastAPI backend and a single-file Vue3/Tailwind HTML frontend. No build steps, no Node.js, no npm modules.

## Prerequisites

- [Ollama](https://ollama.com/) running locally (listening on `http://localhost:11434` by default).
- Python 3.8+
- `python3-venv` (for Debian/Ubuntu based systems)

## Quick Start (Manual Run)

1. **Clone/Download the repository** and navigate to the folder:
   ```bash
   cd /path/to/ollama-benchmark-ui
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn httpx pydantic
   ```

4. **Start the server:**
   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://localhost:5000` (or `http://<your-machine-ip>:5000` if accessing across a network/Tailscale).

## Running as a Background Daemon (Linux / systemd)

If you are running this on a dedicated machine or homelab, you likely want it running in the background at all times. You can set it up as a `systemd` service.

1. **Create the service file:**
   Run the following command, making sure to replace `<YOUR_USER>` and `/path/to/ollama-benchmark-ui` with your actual username and absolute directory path.

   ```bash
   sudo tee /etc/systemd/system/llm-benchmark.service > /dev/null << 'EOF'
   [Unit]
   Description=LLM Benchmark UI Daemon
   After=network.target

   [Service]
   User=<YOUR_USER>
   WorkingDirectory=/path/to/ollama-benchmark-ui
   ExecStart=/path/to/ollama-benchmark-ui/venv/bin/python app.py
   Restart=always
   RestartSec=5
   StandardOutput=syslog
   StandardError=syslog
   SyslogIdentifier=llm-benchmark

   [Install]
   WantedBy=multi-user.target
   EOF
   ```

2. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable llm-benchmark.service
   sudo systemctl start llm-benchmark.service
   ```

3. **Check the status:**
   ```bash
   sudo systemctl status llm-benchmark.service
   ```

### Managing the Daemon

- **View live logs:** `journalctl -u llm-benchmark.service -f`
- **Restart the app:** `sudo systemctl restart llm-benchmark.service`
- **Stop the app:** `sudo systemctl stop llm-benchmark.service`

## File Structure

- `app.py`: The FastAPI backend. Proxies requests to Ollama, handles the SSE stream, and manages VRAM eviction endpoints.
- `index.html`: The entire frontend. Served statically by FastAPI. Contains the Vue3 reactive state, polling logic, and UI styling.
```
