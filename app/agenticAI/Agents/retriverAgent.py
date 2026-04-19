# agents/retriever.py

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class RetrieverAgent:
    """
    RetrieverAgent: Retrieves relevant documents from vector store using adaptive strategies.
    
    This agent implements intelligent document retrieval by:
    - Using MMR (Maximal Marginal Relevance) for diverse results
    - Adapting retrieval parameters based on iteration count
    - Filtering low-quality or irrelevant documents
    - Providing retrieval metadata for evaluation
    """

    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.default_k = 5
        self.default_fetch_k = 20

    def _get_retrieval_params(self, iteration_count: int) -> Dict[str, Any]:
        """
        Adapt retrieval parameters based on iteration count.
        Later iterations cast a wider net to find relevant information.
        
        Args:
            iteration_count: Current iteration number
            
        Returns:
            Dictionary with k and fetch_k parameters
        """
        if iteration_count == 0:
            return {"k": 8, "fetch_k": 20}
        elif iteration_count == 1:
            return {"k": 10, "fetch_k": 30}
        else:
            return {"k": 12, "fetch_k": 40}

    def _assess_document_quality(self, docs: List[Any], query: str) -> Dict[str, Any]:
        """
        Assess the quality and relevance of retrieved documents.
        
        Args:
            docs: List of retrieved documents
            query: The search query used
            
        Returns:
            Dictionary with quality metrics
        """
        if not docs:
            return {
                "has_documents": False,
                "document_count": 0,
                "quality_score": 0.0,
                "assessment": "No documents retrieved"
            }
        
        total_length = sum(len(doc.page_content) for doc in docs)
        avg_length = total_length / len(docs) if docs else 0
        
        quality_score = min(1.0, (len(docs) / 5.0) * (avg_length / 500.0))
        
        assessment = "Good"
        if len(docs) < 3:
            assessment = "Limited documents found"
        elif avg_length < 100:
            assessment = "Documents may be too brief"
        elif len(docs) >= 5 and avg_length > 200:
            assessment = "Excellent document coverage"
        
        return {
            "has_documents": True,
            "document_count": len(docs),
            "quality_score": quality_score,
            "average_doc_length": avg_length,
            "total_content_length": total_length,
            "assessment": assessment
        }

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant documents from vector store using adaptive strategies.
        
        Args:
            state: Current graph state with refined_query and iteration_count
            
        Returns:
            Dictionary with context documents and retrieval metadata
        """
        try:
            refined_query = state.get("refined_query", state.get("query", ""))
            iteration_count = state.get("iteration_count", 0)
            
            if not refined_query:
                logger.warning("No query provided to retriever")
                return {
                    "context": [],
                    "retrieval_metadata": {
                        "status": "error",
                        "message": "No query provided",
                        "has_documents": False,
                        "document_count": 0
                    }
                }
            
            retrieval_params = self._get_retrieval_params(iteration_count)
            
            logger.info(f"Retrieving documents with params: {retrieval_params} for query: '{refined_query}'")
            
            retriever = self.vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs=retrieval_params
            )
            
            docs = retriever.invoke(refined_query)
            
            quality_assessment = self._assess_document_quality(docs, refined_query)
            
            retrieval_metadata = {
                "status": "success",
                "query_used": refined_query,
                "iteration": iteration_count,
                "retrieval_params": retrieval_params,
                **quality_assessment
            }
            
            logger.info(f"Retrieved {len(docs)} documents. Assessment: {quality_assessment['assessment']}")
            
            return {
                "context": docs,
                "retrieval_metadata": retrieval_metadata
            }
            
        except Exception as e:
            logger.error(f"Error in retriever: {str(e)}")
            return {
                "context": [],
                "retrieval_metadata": {
                    "status": "error",
                    "message": f"Retrieval failed: {str(e)}",
                    "has_documents": False,
                    "document_count": 0
                }
            }