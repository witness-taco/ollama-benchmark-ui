import json
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import List

app = FastAPI()
OLLAMA_URL = "http://localhost:11434"

class BenchmarkRequest(BaseModel):
    models: List[str]
    prompt: str

@app.get("/")
async def get_ui():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found.")

@app.get("/api/models")
async def get_models():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to connect to Ollama: {str(e)}")

@app.post("/api/flush")
async def flush_models():
    """Explicitly finds all loaded models and evicts them from VRAM."""
    async with httpx.AsyncClient() as client:
        try:
            # Check currently loaded models
            response = await client.get(f"{OLLAMA_URL}/api/ps")
            response.raise_for_status()
            loaded_models = response.json().get("models", [])
            
            # Send keep_alive 0 to forcefully unload them
            for m in loaded_models:
                await client.post(f"{OLLAMA_URL}/api/generate", json={
                    "model": m.get("name"),
                    "keep_alive": 0
                })
            return {"status": "success", "flushed_count": len(loaded_models)}
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to flush models: {str(e)}")

@app.post("/api/benchmark")
async def run_benchmark(req: BenchmarkRequest, request: Request):
    async def event_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            for model in req.models:
                # Detect if user clicked "Cancel Sequence"
                if await request.is_disconnected():
                    break
                    
                yield f"event: model_start\ndata: {model}\n\n"
                
                payload = {
                    "model": model,
                    "prompt": req.prompt,
                    "stream": True,
                    "keep_alive": 0
                }
                
                try:
                    async with client.stream("POST", f"{OLLAMA_URL}/api/generate", json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            # Break stream instantly if aborted
                            if await request.is_disconnected():
                                break
                            if line:
                                data = json.loads(line)
                                token = data.get("response", "")
                                yield f"event: token\ndata: {json.dumps(token)}\n\n"
                except Exception as e:
                    yield f"event: error\ndata: {json.dumps(str(e))}\n\n"
                
                yield f"event: model_end\ndata: {model}\n\n"
                
                if await request.is_disconnected():
                    break
                    
        yield "event: done\ndata: null\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
