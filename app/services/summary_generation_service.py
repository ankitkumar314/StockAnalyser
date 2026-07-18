from typing import Optional, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services.transcript_service import TranscriptService
from app.controllers.agent_controller import AgentController
from app.models.agent import PDFIngestRequest, BatchQuestionRequest
from app.database.models import ConcallTranscript
import logging

logger = logging.getLogger(__name__)


class SummaryGenerationService:
    """Service for background summary generation using existing RAG system."""
    
    def __init__(self):
        self.agent_controller = AgentController()
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def _generate_summary_for_transcript(self, transcript: ConcallTranscript) -> bool:
        """Generate summary for a single transcript using existing batch_evaluate."""
        try:
            logger.info(f"Starting summary generation for transcript ID: {transcript.id}")
            
            # Update status to processing
            TranscriptService.update_transcript_status(transcript.id, 'processing')
            
            # Ingest PDF to get doc_id
            if not transcript.transcript_url:
                logger.error(f"No transcript URL for transcript {transcript.id}")
                TranscriptService.update_transcript_status(transcript.id, 'failed')
                return False
            
            logger.info(f"Ingesting PDF from URL: {transcript.transcript_url}")
            ingest_request = PDFIngestRequest(pdf_url=transcript.transcript_url)
            ingest_response = self.agent_controller.ingest_pdf(ingest_request)
            doc_id = ingest_response.doc_id
            
            # Use existing batch_evaluate method with 5 predefined questions
            logger.info(f"Running batch evaluation for doc_id: {doc_id}")
            batch_request = BatchQuestionRequest(doc_id=doc_id)
            batch_response = self.agent_controller.batch_evaluate(batch_request)
            
            # Extract answers from batch response
            answers = [qa.answer for qa in batch_response.results]
            
            # Create summary in database with 5 answers
            summary = TranscriptService.create_summary(
                stock_id=transcript.stock_id,
                quarter_date=transcript.quarter_date,
                answer1=answers[0] if len(answers) > 0 else None,
                answer2=answers[1] if len(answers) > 1 else None,
                answer3=answers[2] if len(answers) > 2 else None,
                answer4=answers[3] if len(answers) > 3 else None,
                answer5=answers[4] if len(answers) > 4 else None,
                concall_url=transcript.transcript_url,
                document_id=doc_id
            )
            
            if summary:
                # Update transcript with summary_id and status
                TranscriptService.update_transcript_status(
                    transcript.id, 'completed', summary.id
                )
                logger.info(f"Successfully generated summary for transcript {transcript.id}")
                return True
            else:
                TranscriptService.update_transcript_status(transcript.id, 'failed')
                return False
                
        except Exception as e:
            logger.error(f"Error generating summary for transcript {transcript.id}: {str(e)}")
            TranscriptService.update_transcript_status(transcript.id, 'failed')
            return False
    
    def generate_summary_sync(self, transcript_id: int) -> bool:
        """Synchronously generate summary for a transcript."""
        try:
            transcript = TranscriptService.get_transcript_by_id(transcript_id)
            if not transcript:
                logger.error(f"Transcript not found: {transcript_id}")
                return False
            
            return self._generate_summary_for_transcript(transcript)
            
        except Exception as e:
            logger.error(f"Error in generate_summary_sync: {str(e)}")
            return False
    
    async def generate_summary_async(self, transcript_id: int) -> bool:
        """Asynchronously generate summary for a transcript."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self.generate_summary_sync,
                transcript_id
            )
        except Exception as e:
            logger.error(f"Error in generate_summary_async: {str(e)}")
            return False
    
    def process_pending_transcripts(self, max_count: int = 10) -> Dict:
        """Process pending transcripts in batch."""
        try:
            pending = TranscriptService.get_pending_transcripts(limit=max_count)
            
            if not pending:
                logger.info("No pending transcripts to process")
                return {"processed": 0, "success": 0, "failed": 0}
            
            logger.info(f"Processing {len(pending)} pending transcripts")
            
            results = {"processed": 0, "success": 0, "failed": 0}
            
            for transcript in pending:
                results["processed"] += 1
                if self._generate_summary_for_transcript(transcript):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            
            logger.info(f"Batch processing complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing pending transcripts: {str(e)}")
            return {"processed": 0, "success": 0, "failed": 0, "error": str(e)}
