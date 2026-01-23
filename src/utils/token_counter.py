import tiktoken
from typing import Optional
from ..config.logger import logger


class TokenCounter:
    """Utility for counting tokens in text."""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize token counter.
        
        Args:
            model: Model name for encoding selection
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback to word count * 1.3 approximation
            return int(len(text.split()) * 1.3)
    
    def estimate_cost(self, token_count: int, model: str = "gpt-4o-mini") -> float:
        """
        Estimate cost for given token count.
        
        Args:
            token_count: Number of tokens
            model: Model name for pricing
            
        Returns:
            Estimated cost in USD
        """
        # Pricing per 1K tokens (as of Jan 2026)
        pricing = {
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.00015,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.0015,
        }
        
        rate = pricing.get(model, 0.002)
        return (token_count / 1000) * rate


# Global instance
token_counter = TokenCounter()
