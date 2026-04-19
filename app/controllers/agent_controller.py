from fastapi import HTTPException
from app.models.agent import (
    PDFIngestRequest, PDFIngestResponse, QueryRequest, QueryResponse, 
    BatchQuestionRequest, BatchQuestionResponse, QuestionAnswer,
    BatchJobResponse, BatchJobStatusResponse, JobStatus
)
import uuid
from datetime import datetime
import threading
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
            self.batch_jobs = {}
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
    
    def _run_batch_evaluation(self, job_id: str, request: BatchQuestionRequest):
        """
        Internal method to run batch evaluation in background.
        Updates job status in self.batch_jobs.
        """
        try:
            self.batch_jobs[job_id]["status"] = JobStatus.PROCESSING
            
            if request is None or request.doc_id is None or request.doc_id.strip() == "":
                raise ValueError("Invalid request or doc_id")
            
            STATIC_QUESTIONS = [
                "What are the key business performance highlights discussed in the call, including growth trends, revenue drivers, profitability, and any major changes compared to previous periods?",
                "What are the most important insights and takeaways from management commentary, including strategic priorities, operational improvements, and key drivers of performance?",
                "What is the company’s future outlook as discussed in the call, including growth expectations, expansion plans, new initiatives, and key growth drivers?",
                "What risks, challenges, or uncertainties did management highlight, including market conditions, cost pressures, regulatory risks, or operational constraints?",
                "What major announcements, strategic initiatives, or upcoming catalysts were discussed that could significantly impact the company’s future performance?",
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
            total_questions = len(STATIC_QUESTIONS)
            
            for idx, question in enumerate(STATIC_QUESTIONS):
                self.batch_jobs[job_id]["progress"] = f"Processing question {idx + 1}/{total_questions}"
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
            
            self.batch_jobs[job_id]["status"] = JobStatus.COMPLETED
            self.batch_jobs[job_id]["result"] = response
            self.batch_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Batch job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in batch job {job_id}: {str(e)}")
            self.batch_jobs[job_id]["status"] = JobStatus.FAILED
            self.batch_jobs[job_id]["error"] = str(e)
            self.batch_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
    
    def batch_evaluate_async(self, request: BatchQuestionRequest) -> BatchJobResponse:
        """
        Start batch evaluation as a background job.
        Returns immediately with job_id for status tracking.
        """
        try:
            if request is None:
                raise HTTPException(status_code=400, detail="Request cannot be None")
            
            if request.doc_id is None or request.doc_id.strip() == "":
                raise HTTPException(status_code=400, detail="Document ID cannot be empty")
            
            vectorstore = self.vector_db_manager.load_vector_store(request.doc_id)
            if vectorstore is None:
                raise HTTPException(status_code=404, detail=f"Vector store not found for doc_id: {request.doc_id}")
            
            job_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            
            self.batch_jobs[job_id] = {
                "status": JobStatus.PENDING,
                "doc_id": request.doc_id,
                "created_at": created_at,
                "progress": "Job queued",
                "result": None,
                "error": None,
                "completed_at": None
            }
            
            thread = threading.Thread(
                target=self._run_batch_evaluation,
                args=(job_id, request),
                daemon=True
            )
            thread.start()
            
            logger.info(f"Started batch job {job_id} for doc_id: {request.doc_id}")
            
            return BatchJobResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                doc_id=request.doc_id,
                message="Batch evaluation started. Use job_id to check status.",
                created_at=created_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error starting batch evaluation: {str(e)}")
    
    def get_batch_job_status(self, job_id: str) -> BatchJobStatusResponse:
        """
        Get the status of a batch evaluation job.
        """
        try:
            if job_id not in self.batch_jobs:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            
            job = self.batch_jobs[job_id]
            
            return BatchJobStatusResponse(
                job_id=job_id,
                status=job["status"],
                doc_id=job["doc_id"],
                progress=job.get("progress"),
                result=job.get("result"),
                error=job.get("error"),
                created_at=job["created_at"],
                completed_at=job.get("completed_at")
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")
    
    def list_batch_jobs(self):
        """
        List all batch jobs.
        """
        try:
            jobs = []
            for job_id, job_data in self.batch_jobs.items():
                jobs.append({
                    "job_id": job_id,
                    "status": job_data["status"],
                    "doc_id": job_data["doc_id"],
                    "created_at": job_data["created_at"],
                    "completed_at": job_data.get("completed_at")
                })
            return {"total_jobs": len(jobs), "jobs": jobs}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error listing jobs: {str(e)}")
    
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
