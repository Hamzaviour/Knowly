from typing import Dict, Any

# Approximate Pricing per 1M tokens (USD)
MODEL_PRICING = {
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "anthropic/claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "groq/llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "groq/llama-3.1-8b-instant": {"input": 0.05, "output": 0.08}
}

class CostTracker:
    @staticmethod
    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 2.0})
        cost_in = (prompt_tokens / 1_000_000.0) * pricing["input"]
        cost_out = (completion_tokens / 1_000_000.0) * pricing["output"]
        return round(cost_in + cost_out, 6)
