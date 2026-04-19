from fastapi import HTTPException
from app.models.agent import PDFIngestRequest, PDFIngestResponse, QueryRequest, QueryResponse, BatchQuestionRequest, BatchQuestionResponse, QuestionAnswer
from app.agenticAI.vectorDB.main import VectorDBManager
from app.agenticAI.llm_Model import LLMFactory
from app.agenticAI.Agents.plannerAgent import PlannerAgent
from app.agenticAI.Agents.retriverAgent import RetrieverAgent
from app.agenticAI.Agents.answerAgent import AnswerAgent
from app.agenticAI.Agents.evaluatorAgent import EvaluatorAgent
from app.agenticAI.langraph import RAGGraph
from app.agenticAI.langsmith_config import langsmith_config
import logging

logger = logging.getLogger(__name__)


class AgentController:
    def __init__(self):
        try:
            self.vector_db_manager = VectorDBManager()
        except Exception as e:
            raise Exception(f"Error initializing AgentController: {str(e)}")
    
    def ingest_pdf(self, request: PDFIngestRequest) -> PDFIngestResponse:
        try:
            if request is None:
                raise HTTPException(status_code=400, detail="Request cannot be None")
            
            if request.pdf_url is None or request.pdf_url.strip() == "":
                raise HTTPException(status_code=400, detail="PDF URL cannot be empty")
            
            doc_id, vectorstore, chunks = self.vector_db_manager.ingest_and_store(request.pdf_url)
            
            
            if doc_id is None:
                raise HTTPException(status_code=500, detail="Failed to create vector store")
            
            response = PDFIngestResponse(
                doc_id=doc_id,
                message="PDF ingested successfully",
                chunks_count=len(chunks)
            )
            
            return response
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error ingesting PDF: {str(e)}")
    
    def query(self, request: QueryRequest) -> QueryResponse:
        try:
            if request is None:
                raise HTTPException(status_code=400, detail="Request cannot be None")
            
            if request.query is None or request.query.strip() == "":
                raise HTTPException(status_code=400, detail="Query cannot be empty")
            
            if request.doc_id is None or request.doc_id.strip() == "":
                raise HTTPException(status_code=400, detail="Document ID cannot be empty")
            
            vectorstore = self.vector_db_manager.load_vector_store(request.doc_id)
            
            if vectorstore is None:
                raise HTTPException(status_code=404, detail=f"Vector store not found for doc_id: {request.doc_id}")
            
            run_metadata = {
                "doc_id": request.doc_id,
                "query": request.query,
                "endpoint": "query"
            }
            
            planner = PlannerAgent(LLMFactory.get_deepseek(
                metadata={**run_metadata, "agent": "planner"}
            ))
            retriever = RetrieverAgent(vectorstore)
            answerer = AnswerAgent(LLMFactory.get_deepseek(
                metadata={**run_metadata, "agent": "answerer"}
            ))
            evaluator = EvaluatorAgent(LLMFactory.get_evaluator_model(
                metadata={**run_metadata, "agent": "evaluator"}
            ))
            
            graph = RAGGraph(planner, retriever, answerer, evaluator).compile()
            
            langsmith_run_config = langsmith_config.get_run_config(
                run_name=f"query-{request.doc_id[:8]}",
                tags=["rag", "query", "production"],
                metadata=run_metadata
            )
            
            result = graph.invoke(
                {
                    "query": request.query,
                    "iteration_count": 0,
                    "max_iterations": 3,
                    "messages": [],
                    "previous_contexts": [],
                    "previous_answers": [],
                    "memory": {}
                },
                config=langsmith_run_config if langsmith_run_config else None
            )
            
            if result is None or "final_answer" not in result:
                raise HTTPException(status_code=500, detail="Failed to get answer from agent")
            
            response = QueryResponse(
                query=request.query,
                answer=result["final_answer"],
                doc_id=request.doc_id
            )
            
            return response
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

            
    def get_graph_visualization(self):
        try:
            planner = PlannerAgent(LLMFactory.get_deepseek(enable_tracing=False))
            retriever = RetrieverAgent(None)  
            answerer = AnswerAgent(LLMFactory.get_deepseek(enable_tracing=False))
            evaluator = EvaluatorAgent(LLMFactory.get_evaluator_model(enable_tracing=False))

            graph = RAGGraph(planner, retriever, answerer, evaluator)
            graph.save_graph_visualization()

            return {"message": "Graph saved to rag_graph.png"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating graph: {str(e)}")
    
    def batch_evaluate(self, request: BatchQuestionRequest) -> BatchQuestionResponse:
        try:
            if request is None:
                raise HTTPException(status_code=400, detail="Request cannot be None")
            
            if request.doc_id is None or request.doc_id.strip() == "":
                raise HTTPException(status_code=400, detail="Document ID cannot be empty")
            
            STATIC_QUESTIONS = [
                "What is the main topic or subject of this document?",
                "What are the key findings or conclusions presented?",
                "Who are the primary stakeholders or entities mentioned?",
                "What is the time period or date range covered in this document?",
                "What are the main recommendations or action items?",
                "What data or evidence supports the main claims?"
            ]
            
            vectorstore = self.vector_db_manager.load_vector_store(request.doc_id)
            
            if vectorstore is None:
                raise HTTPException(status_code=404, detail=f"Vector store not found for doc_id: {request.doc_id}")
            
            run_metadata = {
                "doc_id": request.doc_id,
                "endpoint": "batch_evaluate"
            }
            
            planner = PlannerAgent(LLMFactory.get_deepseek(
                metadata={**run_metadata, "agent": "planner"}
            ))
            retriever = RetrieverAgent(vectorstore)
            answerer = AnswerAgent(LLMFactory.get_deepseek(
                metadata={**run_metadata, "agent": "answerer"}
            ))
            evaluator = EvaluatorAgent(LLMFactory.get_evaluator_model(
                metadata={**run_metadata, "agent": "evaluator"}
            ))
            
            graph = RAGGraph(planner, retriever, answerer, evaluator).compile()
            
            results = []
            
            for idx, question in enumerate(STATIC_QUESTIONS):
                try:
                    langsmith_run_config = langsmith_config.get_run_config(
                        run_name=f"batch-q{idx+1}-{request.doc_id[:8]}",
                        tags=["rag", "batch", "evaluation"],
                        metadata={**run_metadata, "question_index": idx}
                    )
                    
                    result = graph.invoke(
                        {
                            "query": question,
                            "iteration_count": 0,
                            "max_iterations": 3,
                            "messages": [],
                            "previous_contexts": [],
                            "previous_answers": [],
                            "memory": {}
                        },
                        config=langsmith_run_config if langsmith_run_config else None
                    )
                    
                    if result is None or "final_answer" not in result:
                        answer = "Failed to generate answer"
                        iteration_count = 0
                    else:
                        answer = result["final_answer"]
                        iteration_count = result.get("iteration_count", 0)
                    
                    results.append(QuestionAnswer(
                        question=question,
                        answer=answer,
                        iteration_count=iteration_count
                    ))
                    
                except Exception as e:
                    results.append(QuestionAnswer(
                        question=question,
                        answer=f"Error: {str(e)}",
                        iteration_count=0
                    ))
            
            response = BatchQuestionResponse(
                doc_id=request.doc_id,
                total_questions=len(STATIC_QUESTIONS),
                results=results
            )
            
            return response
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in batch evaluation: {str(e)}")
    
    def get_cost_summary(self):
        """
        Get summary of LLM costs and token usage.
        
        Returns:
            Dictionary with cost and usage statistics
        """
        try:
            summary = LLMFactory.get_cost_summary()
            return {
                "status": "success",
                "langsmith_enabled": langsmith_config.enabled,
                "langsmith_project": langsmith_config.project_name if langsmith_config.enabled else None,
                **summary
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting cost summary: {str(e)}")
    
    def predict_query_cost(self, query: str, doc_id: str):
        """
        Predict cost for a query before execution.
        
        Args:
            query: The query string
            doc_id: Document ID
            
        Returns:
            Cost prediction
        """
        try:
            estimated_input = len(query.split()) * 2 * 3
            estimated_output = 500
            
            planner_cost = LLMFactory.predict_cost("deepseek-reasoner", estimated_input, 100)
            answerer_cost = LLMFactory.predict_cost("deepseek-reasoner", estimated_input * 5, estimated_output)
            evaluator_cost = LLMFactory.predict_cost("deepseek-chat", estimated_input * 3, 200)
            
            total_predicted = (
                planner_cost["predicted_cost"]["total"] +
                answerer_cost["predicted_cost"]["total"] +
                evaluator_cost["predicted_cost"]["total"]
            )
            
            return {
                "status": "success",
                "query": query,
                "doc_id": doc_id,
                "predictions": {
                    "planner": planner_cost,
                    "answerer": answerer_cost,
                    "evaluator": evaluator_cost
                },
                "total_predicted_cost": round(total_predicted, 6),
                "note": "This is an estimate. Actual costs may vary based on context size and iterations."
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error predicting cost: {str(e)}")
    
    def reset_cost_tracking(self):
        """
        Reset cost tracking data.
        
        Returns:
            Success message
        """
        try:
            LLMFactory.reset_cost_tracker()
            return {
                "status": "success",
                "message": "Cost tracking data has been reset"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error resetting cost tracker: {str(e)}")
