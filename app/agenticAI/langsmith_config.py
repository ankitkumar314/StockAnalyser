import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LangSmithConfig:
    """
    LangSmith configuration for tracing, monitoring, and cost analysis.
    
    This class manages LangSmith integration for:
    - Trace capture and visualization
    - Performance monitoring
    - Cost tracking and prediction
    - Error analysis
    """
    
    def __init__(self):
        self.enabled = self._check_langsmith_enabled()
        self.project_name = os.getenv("LANGCHAIN_PROJECT", "rag-agent-system")
        self.endpoint = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
        self.api_key = os.getenv("LANGCHAIN_API_KEY")
        
        if self.enabled:
            self._setup_environment()
            logger.info(f"LangSmith enabled for project: {self.project_name}")
        else:
            logger.warning("LangSmith is disabled. Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY to enable.")
    
    def _check_langsmith_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled via environment variables."""
        tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        has_api_key = bool(os.getenv("LANGCHAIN_API_KEY"))
        return tracing_enabled and has_api_key
    
    def _setup_environment(self):
        """Set up LangSmith environment variables."""
        try:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = self.project_name
            os.environ["LANGCHAIN_ENDPOINT"] = self.endpoint
            if self.api_key:
                os.environ["LANGCHAIN_API_KEY"] = self.api_key
        except Exception as e:
            logger.error(f"Error setting up LangSmith environment: {str(e)}")
    
    def get_run_config(self, run_name: Optional[str] = None, tags: Optional[list] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get configuration for a LangSmith run.
        
        Args:
            run_name: Name for this run
            tags: List of tags for categorization
            metadata: Additional metadata for the run
            
        Returns:
            Configuration dictionary for LangChain invocation
        """
        if not self.enabled:
            return {}
        
        config = {
            "run_name": run_name or "rag-query",
            "tags": tags or ["rag", "agent", "production"],
            "metadata": metadata or {}
        }
        
        return config
    
    def get_callbacks(self):
        """
        Get LangSmith callbacks for tracing.
        
        Returns:
            List of callbacks if enabled, empty list otherwise
        """
        if not self.enabled:
            return []
        
        try:
            from langsmith import Client
            client = Client(api_key=self.api_key, api_url=self.endpoint)
            return []
        except ImportError:
            logger.warning("langsmith package not installed. Install with: pip install langsmith")
            return []
        except Exception as e:
            logger.error(f"Error creating LangSmith callbacks: {str(e)}")
            return []


langsmith_config = LangSmithConfig()
