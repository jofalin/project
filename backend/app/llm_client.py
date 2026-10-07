from __future__ import annotations
import hashlib
import json
import httpx
from .config import get_settings
from .v1_schemas import OperatorAdvisory

class OpenAICompatibleAdvisoryClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.llm_base_url
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model

    async def generate_advisory(self, context) -> tuple[str, dict]:
        if not self.base_url or not self.api_key:
            raise RuntimeError("LLM_BASE_URL and LLM_API_KEY are required for live model orchestration")
        schema = OperatorAdvisory.model_json_schema()
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_schema", "json_schema": {"name": "operator_advisory", "strict": True, "schema": schema}},
            "messages": [
                {"role": "system", "content": "Return JSON only and match the supplied schema. Never issue autonomous physical-world commands."},
                {"role": "user", "content": json.dumps({"telemetry": context.telemetry, "weather": context.weather, "gate_throughput": context.gate_throughput, "sop_documents": context.sop_documents}, separators=(",", ":"))},
            ],
        }
        prompt_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        trace = {"model": self.model, "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(), "tooling": ["telemetry", "weather", "gate_throughput", "sop_rag"]}
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(self.base_url.rstrip("/") + "/chat/completions", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=payload)
            response.raise_for_status()
            body = response.json()
        content = body["choices"][0]["message"]["content"]
        OperatorAdvisory.model_validate_json(content)
        trace["response_id"] = body.get("id")
        return content, trace
