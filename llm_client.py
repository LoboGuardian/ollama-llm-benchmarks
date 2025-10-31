# llm_client.py
import ollama
from time import perf_counter

class OllamaClient:
    """
    Handles all interactions with the local Ollama server.
    Manages client connection, request execution, and initial performance timing.
    """
    def __init__(self, host: str):
        # The ollama client abstracts the HTTP logic (Dependency Inversion preparation)
        self.client = ollama.Client(host=host)

    def generate_response(self, model: str, prompt: str) -> dict:
        """
        Generates a streaming response, measuring TTFT, latency, and T/s.
        
        Args:
            model: The Ollama model tag to use.
            prompt: The text prompt for the model.

        Returns:
            A dictionary containing the response text and performance metrics.
        """
        start_time = perf_counter()
        
        # Use generate API for consistent measurement across models
        response_stream = self.client.generate(
            model=model,
            prompt=prompt,
            stream=True
        )

        first_token_time = None
        full_response = ""
        final_chunk = {}
        
        # Stream the response to measure Time-to-First-Token (TTFT)
        for chunk in response_stream:
            # Capture the timestamp the very first token is received
            if not first_token_time:
                first_token_time = perf_counter()
            
            full_response += chunk.get('response', '')
            final_chunk = chunk # Keep the last chunk to extract metadata (tokens, load time)
            
            if chunk.get('done'):
                break

        end_time = perf_counter()
        
        # Calculate metrics
        total_latency = end_time - start_time
        time_to_first_token = (first_token_time - start_time) if first_token_time else None
        
        # Ollama provides useful metadata in the final chunk
        tokens_generated = final_chunk.get('eval_count', 0)

        # DRY Principle: Calculate T/s once and store it.
        tokens_per_second = tokens_generated / total_latency if tokens_generated and total_latency > 0 else 0

        return {
            "prompt": prompt,
            "response_text": full_response,
            "time_to_first_token_s": round(time_to_first_token, 4),
            "total_latency_s": round(total_latency, 4),
            "tokens_generated": tokens_generated,
            "tokens_per_second": round(tokens_per_second, 2),
            "ollama_metadata": final_chunk
        }