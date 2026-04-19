import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CostTracker:
    """
    Track and predict costs for LLM API calls.
    
    This class provides:
    - Token usage tracking
    - Cost calculation based on model pricing
    - Cost prediction for queries
    - Usage analytics
    """
    
    PRICING = {
        "deepseek-chat": {
            "input": 0.14 / 1_000_000,
            "output": 0.28 / 1_000_000,
            "cache_hit": 0.014 / 1_000_000
        },
        "deepseek-reasoner": {
            "input": 0.55 / 1_000_000,
            "output": 2.19 / 1_000_000,
            "cache_hit": 0.014 / 1_000_000
        }
    }
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_tokens = 0
        self.total_cost = 0.0
        self.runs = []
    
    def track_run(self, model: str, input_tokens: int, output_tokens: int, 
                  cache_tokens: int = 0, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Track a single LLM run and calculate its cost.
        
        Args:
            model: Model name (e.g., "deepseek-chat")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_tokens: Number of cached tokens
            metadata: Additional metadata about the run
            
        Returns:
            Dictionary with cost information
        """
        try:
            pricing = self.PRICING.get(model, self.PRICING["deepseek-chat"])
            
            input_cost = input_tokens * pricing["input"]
            output_cost = output_tokens * pricing["output"]
            cache_cost = cache_tokens * pricing["cache_hit"]
            
            total_cost = input_cost + output_cost + cache_cost
            
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_cache_tokens += cache_tokens
            self.total_cost += total_cost
            
            run_info = {
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "cache": cache_tokens,
                    "total": input_tokens + output_tokens
                },
                "cost": {
                    "input": round(input_cost, 6),
                    "output": round(output_cost, 6),
                    "cache": round(cache_cost, 6),
                    "total": round(total_cost, 6)
                },
                "metadata": metadata or {}
            }
            
            self.runs.append(run_info)
            
            logger.info(f"Cost tracked: ${total_cost:.6f} for {model} ({input_tokens} in, {output_tokens} out)")
            
            return run_info
            
        except Exception as e:
            logger.error(f"Error tracking cost: {str(e)}")
            return {
                "error": str(e),
                "cost": {"total": 0.0}
            }
    
    def predict_cost(self, model: str, estimated_input_tokens: int, 
                     estimated_output_tokens: int) -> Dict[str, Any]:
        """
        Predict cost for a future LLM call.
        
        Args:
            model: Model name
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
            
        Returns:
            Dictionary with predicted cost
        """
        try:
            pricing = self.PRICING.get(model, self.PRICING["deepseek-chat"])
            
            predicted_input_cost = estimated_input_tokens * pricing["input"]
            predicted_output_cost = estimated_output_tokens * pricing["output"]
            predicted_total = predicted_input_cost + predicted_output_cost
            
            return {
                "model": model,
                "estimated_tokens": {
                    "input": estimated_input_tokens,
                    "output": estimated_output_tokens,
                    "total": estimated_input_tokens + estimated_output_tokens
                },
                "predicted_cost": {
                    "input": round(predicted_input_cost, 6),
                    "output": round(predicted_output_cost, 6),
                    "total": round(predicted_total, 6)
                }
            }
        except Exception as e:
            logger.error(f"Error predicting cost: {str(e)}")
            return {"error": str(e)}
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tracked runs.
        
        Returns:
            Dictionary with usage and cost summary
        """
        return {
            "total_runs": len(self.runs),
            "total_tokens": {
                "input": self.total_input_tokens,
                "output": self.total_output_tokens,
                "cache": self.total_cache_tokens,
                "total": self.total_input_tokens + self.total_output_tokens
            },
            "total_cost": round(self.total_cost, 6),
            "average_cost_per_run": round(self.total_cost / len(self.runs), 6) if self.runs else 0.0,
            "runs": self.runs[-10:]
        }
    
    def reset(self):
        """Reset all tracking data."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_tokens = 0
        self.total_cost = 0.0
        self.runs = []
        logger.info("Cost tracker reset")


cost_tracker = CostTracker()
