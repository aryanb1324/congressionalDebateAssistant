import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLMClient:
    def generate(self, messages):
        raise NotImplementedError

class OpenAIClient(LLMClient):
    def __init__(self, model=None):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing in environment/.env")
        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

    def generate(self, messages):
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.85,       # creative
            top_p=0.9,
            presence_penalty=0.4,
            frequency_penalty=0.1,
        )
        return resp.choices[0].message.content

class OllamaClient(LLMClient):
    def __init__(self, model=None):
        self.base = "http://127.0.0.1:11434"
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, messages):
        # Flatten OpenAI-style messages to a single chat for Ollama
        text = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                text.append(f"[SYSTEM]\n{content}\n")
            else:
                text.append(content)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "\n".join(text)}],
            "stream": False,
            "options": {"temperature": 0.95, "top_p": 0.9},
        }
        r = requests.post(f"{self.base}/api/chat", json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
        # Newer Ollama returns conversation; fallback to message.content if present
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        # Some versions stream chunks; join them if present
        if "content" in data:
            return data["content"]
        return str(data)

def get_llm_client() -> LLMClient:
    provider = (os.getenv("LLM_PROVIDER", "openai") or "openai").lower()
    if provider == "ollama":
        return OllamaClient()
    return OpenAIClient()
