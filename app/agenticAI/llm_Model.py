from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import logging
from typing import Optional, Dict, Any
from langchain_core.callbacks.base import BaseCallbackHandler


from app.agenticAI.langsmith_config import langsmith_config
from app.agenticAI.cost_tracker import cost_tracker



load_dotenv()
logger = logging.getLogger(__name__)

class CostTrackingCallback(BaseCallbackHandler):
    """Callback handler to track token usage and costs."""
    
    def __init__(self, model_name: str, run_metadata: Optional[Dict[str, Any]] = None):
        self.model_name = model_name
        self.run_metadata = run_metadata or {}
        self.input_tokens = 0
        self.output_tokens = 0
    
    def on_llm_end(self, response, **kwargs):
        """Track tokens when LLM call completes."""
        try:
            if hasattr(response, 'llm_output') and response.llm_output:
                token_usage = response.llm_output.get('token_usage', {})
                self.input_tokens = token_usage.get('prompt_tokens', 0)
                self.output_tokens = token_usage.get('completion_tokens', 0)
                cache_tokens = token_usage.get('prompt_cache_hit_tokens', 0)
                
                cost_tracker.track_run(
                    model=self.model_name,
                    input_tokens=self.input_tokens,
                    output_tokens=self.output_tokens,
                    cache_tokens=cache_tokens,
                    metadata=self.run_metadata
                )
        except Exception as e:
            logger.error(f"Error tracking cost in callback: {str(e)}")

class LLMFactory:

    @staticmethod
    def get_deepseek(model="deepseek-chat", temperature=0, 
                     enable_tracing=True, run_name: Optional[str] = None,
                     tags: Optional[list] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Get DeepSeek LLM with LangSmith tracing and cost tracking.
        
        Args:
            model: Model name (deepseek-reasoner or deepseek-chat)
            temperature: Temperature for generation
            enable_tracing: Enable LangSmith tracing
            run_name: Name for LangSmith run
            tags: Tags for categorization
            metadata: Additional metadata
            
        Returns:
            ChatOpenAI instance with callbacks configured
        """
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key is None or api_key.strip() == "":
                raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
            
            callbacks = []
            
            if enable_tracing and langsmith_config.enabled:
                callbacks.extend(langsmith_config.get_callbacks())
            
            cost_callback = CostTrackingCallback(
                model_name=model,
                run_metadata=metadata or {"agent": "planner/answerer"}
            )
            callbacks.append(cost_callback)
            
            llm = ChatOpenAI(
                model=model,
                base_url="https://api.deepseek.com",
                api_key=api_key,
                temperature=temperature,
                max_retries=2,
                callbacks=callbacks if callbacks else None
            )
            
            if enable_tracing and langsmith_config.enabled:
                logger.info(f"LangSmith tracing enabled for {model}")
            
            return llm
            
        except Exception as e:
            raise Exception(f"Error initializing DeepSeek model: {str(e)}")

    @staticmethod
    def get_evaluator_model(enable_tracing=True, run_name: Optional[str] = None,
                           tags: Optional[list] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Get evaluator LLM with LangSmith tracing and cost tracking.
        
        Args:
            enable_tracing: Enable LangSmith tracing
            run_name: Name for LangSmith run
            tags: Tags for categorization
            metadata: Additional metadata
            
        Returns:
            ChatOpenAI instance with callbacks configured
        """
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key is None or api_key.strip() == "":
                raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
            
            callbacks = []
            
            if enable_tracing and langsmith_config.enabled:
                callbacks.extend(langsmith_config.get_callbacks())
            
            cost_callback = CostTrackingCallback(
                model_name="deepseek-chat",
                run_metadata=metadata or {"agent": "evaluator"}
            )
            callbacks.append(cost_callback)
            
            llm = ChatOpenAI(
                model="deepseek-reasoner",
                base_url="https://api.deepseek.com",
                api_key=api_key,
                temperature=0,
                max_retries=2,
                callbacks=callbacks if callbacks else None
            )
            
            if enable_tracing and langsmith_config.enabled:
                logger.info("LangSmith tracing enabled for evaluator model")
            
            return llm
            
        except Exception as e:
            raise Exception(f"Error initializing evaluator model: {str(e)}")
    
    @staticmethod
    def get_cost_summary() -> Dict[str, Any]:
        """Get summary of all LLM costs tracked."""
        return cost_tracker.get_summary()
    
    @staticmethod
    def predict_cost(model: str, estimated_input_tokens: int, 
                    estimated_output_tokens: int) -> Dict[str, Any]:
        """Predict cost for a future LLM call."""
        return cost_tracker.predict_cost(model, estimated_input_tokens, estimated_output_tokens)
    
    @staticmethod
    def reset_cost_tracker():
        """Reset cost tracking data."""
        cost_tracker.reset()