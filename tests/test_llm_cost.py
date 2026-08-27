# tests/test_llm_cost.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama
from memory.trajectory_store.llm_cost import extract_llm_cost

response = ollama.generate(model="qwen2.5-coder:7b", prompt="Say hello in one word.")
result = extract_llm_cost(response)
print(result)
assert result["completion_tokens"] > 0, "Expected non-zero completion tokens for a real response"
assert result["total_duration_seconds"] > 0, "Expected non-zero duration for a real response"
print("PASS: extracted real cost metadata from a live Ollama call")