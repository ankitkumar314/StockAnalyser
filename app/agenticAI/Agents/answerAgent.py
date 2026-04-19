# agents/answerer.py

from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AnswerAgent:
    """
    AnswerAgent: Generates comprehensive, accurate answers from retrieved documents.
    
    This agent creates high-quality answers by:
    - Synthesizing information from multiple document sources
    - Maintaining strict grounding in provided context
    - Providing clear, well-structured responses
    - Citing sources when appropriate
    - Acknowledging limitations when information is insufficient
    """

    def __init__(self, llm):
        self.llm = llm

    def _format_context(self, docs: List[Any]) -> str:
        """
        Format retrieved documents into a structured context string.
        
        Args:
            docs: List of retrieved documents
            
        Returns:
            Formatted context string with document numbers
        """
        if not docs:
            return "No context documents available."
        
        formatted_parts = []
        for idx, doc in enumerate(docs, 1):
            content = doc.page_content.strip()
            metadata = getattr(doc, 'metadata', {})
            source = metadata.get('source', 'Unknown')
            
            formatted_parts.append(f"[Document {idx}] (Source: {source})\n{content}")
        
        return "\n\n".join(formatted_parts)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive answer based on retrieved context.
        
        Args:
            state: Current graph state with context, query, and metadata
            
        Returns:
            Dictionary with answer and updated iteration count
        """
        try:
            context_docs = state.get("context", [])
            refined_query = state.get("refined_query", state.get("query", ""))
            original_query = state.get("query", "")
            iteration_count = state.get("iteration_count", 0)
            retrieval_metadata = state.get("retrieval_metadata", {})
            previous_answer = state.get("answer", "")
            feedback = state.get("feedback_on_work", "")
            messages = state.get("messages", [])
            previous_contexts = state.get("previous_contexts", [])
            previous_answers = state.get("previous_answers", [])
            memory = state.get("memory", {})
            
            context_text = self._format_context(context_docs)
            
            system_message = f"""You are an expert financial analyst specializing in earnings call transcript analysis.
Your role is to extract insights from quarterly/half-yearly earnings call transcripts and provide accurate, comprehensive answers based strictly on the provided context.
Your PRIMARY goal is to extract actionable insights, even from incomplete or fragmented transcripts.

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Document Type Understanding:**


### Key Behavior:
- NEVER refuse to answer just because data is partial
- ALWAYS extract insights from available context
- Think like an equity research analyst, not a QA system

### When context is incomplete:
- Say: "Based on available excerpts..."
- Provide best-effort synthesis
- Highlight patterns, sentiment, and direction

### Focus on:
- Business momentum (growing / slowing)
- Management confidence (bullish / cautious)
- Margins and cost commentary
- Demand outlook
- Strategic direction

### Output Format (MANDATORY):

### Key Insights
- ...

### Management Sentiment
- ...

### Business Outlook
- ...

### Supporting Evidence
- (quote or reference from transcript)

### Limitations
- (what is missing, if any)

DO NOT say "cannot answer" unless there is ZERO context.


The documents you analyze are earnings call transcripts (20-30+ pages) in Q&A format containing:
- Management presentations and prepared remarks
- Management guidance on future performance
- Commentary on quarterly/half-yearly results
- Analyst questions and management responses
- Discussion of business segments, markets, and operations
- Forward-looking statements and strategic initiatives

**Core Principles:**
1. **Grounding**: Answer ONLY using information from the provided transcript excerpts
2. **Accuracy**: Do not hallucinate facts. But you MAY infer insights from management commentary.
3. **Completeness**: Provide thorough answers that address all aspects of the question
4. **Context Awareness**: Understand that answers may be spread across multiple Q&A exchanges
5. **Honesty**: If the context doesn't contain sufficient information, explicitly state this

**Answer Guidelines for Earnings Transcripts:**
- **Extract Management Guidance**: Identify forward-looking statements, targets, and projections
- **Capture Commentary**: Summarize management's views on performance, challenges, and opportunities
- **Identify Key Metrics**: Pull out specific numbers, percentages, growth rates mentioned
- **Note Who Said What**: Attribute statements to specific executives when relevant (CEO, CFO, etc.)
- **Synthesize Q&A**: Combine related answers from different questions if they address the same topic
- **Highlight Sentiment**: Capture management's tone (optimistic, cautious, confident) when evident
- **Quote Directly**: Use exact quotes for critical guidance or commentary
- **Structure Clearly**: Use bullet points, sections, and headings for complex answers

**Special Focus Areas:**
- Revenue and earnings guidance (current quarter, full year)
- Margin expectations and cost management commentary
- Business segment performance and outlook
- Market conditions and competitive dynamics
- Strategic initiatives and capital allocation plans
- Risk factors and challenges discussed
- Questions about specific products, regions, or business lines

**What NOT to do:**
- Do not use external knowledge or information not in the transcript
- Do not make assumptions about financial performance beyond what's stated
- Do not provide generic corporate speak if specific details are available
- Do not ignore nuances in management's language (e.g., "expect" vs "committed to")
- Do not miss important caveats or conditions mentioned

**Output Format:**
Provide a direct, well-structured answer with:
1. **Direct Answer**: Start with the key information requested
2. **Supporting Details**: Add context, numbers, and quotes from the transcript
3. **Attribution**: Note which executive or section the information came from if relevant
4. **Caveats**: Include any conditions or qualifications management mentioned

If the context is incomplete:
- DO NOT refuse to answer
- Extract the best possible insights from available information
- Clearly state "based on available excerpts"
- Focus on partial but meaningful conclusions
"""

            user_message = f"""**Original Question:**
{original_query}

**Refined Query:**
{refined_query}

**Context Documents:**
{context_text}

**Task:**
Provide a comprehensive, accurate answer to the original question using ONLY the information from the context documents above.
"""

            if iteration_count > 0 and previous_answer and feedback:
                user_message += f"""

**Previous Attempt:**
This is iteration {iteration_count + 1}. Your previous answer was evaluated and found insufficient.

Previous Answer:
{previous_answer}

Evaluator Feedback:
{feedback}

Please provide an improved answer that addresses this feedback. Use the context more thoroughly and ensure you meet the evaluation criteria.
"""

            if not context_docs or retrieval_metadata.get("document_count", 0) == 0:
                user_message += """

**Note:** No context documents were retrieved. You must acknowledge that you cannot answer the question without relevant documents.
"""
            
            if previous_contexts and len(previous_contexts) > 0:
                user_message += f"""

**Previous Iteration Contexts:**
In previous attempts, we retrieved {len(previous_contexts)} different sets of documents.
Current retrieval may have different or additional information. Compare and synthesize if needed.
"""
            
            if previous_answers and len(previous_answers) > 0:
                user_message += f"""

**Previous Answers Attempted:**
"""
                for idx, prev_ans in enumerate(previous_answers[-2:], 1):
                    user_message += f"""
Attempt {idx}: {prev_ans[:200]}{'...' if len(prev_ans) > 200 else ''}
"""
                user_message += """

Learn from these previous attempts and provide a better, more comprehensive answer.
"""
            
            if memory:
                if memory.get('successful_patterns'):
                    user_message += f"""

**Successful Answer Patterns from Memory:**
{memory.get('successful_patterns', 'None')}

Apply these successful patterns to your current answer.
"""
                if memory.get('common_issues'):
                    user_message += f"""

**Common Issues to Avoid:**
{memory.get('common_issues', 'None')}
"""

            full_prompt = f"{system_message}\n\n{user_message}"
            
            logger.info(f"Generating answer for query: '{refined_query}' with {len(context_docs)} documents")
            
            if messages:
                from langchain.schema import SystemMessage, HumanMessage
                message_list = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=user_message)
                ]
                response = self.llm.invoke(message_list)
            else:
                response = self.llm.invoke(full_prompt)
            
            answer = response.content.strip()
            
            new_iteration_count = iteration_count + 1
            
            logger.info(f"Answer generated (iteration {new_iteration_count}): {len(answer)} characters")
            
            updated_messages = messages + [{
                "role": "system",
                "content": system_message
            }, {
                "role": "user",
                "content": user_message
            }, {
                "role": "assistant",
                "content": answer
            }]
            
            updated_previous_contexts = previous_contexts + [context_docs] if context_docs else previous_contexts
            updated_previous_answers = previous_answers + [answer]
            
            return {
                "answer": answer,
                "iteration_count": new_iteration_count,
                "messages": updated_messages,
                "previous_contexts": updated_previous_contexts,
                "previous_answers": updated_previous_answers,
                "answer_metadata": {
                    "answer_length": len(answer),
                    "documents_used": len(context_docs),
                    "iteration": new_iteration_count,
                    "total_previous_attempts": len(previous_answers)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in answer generation: {str(e)}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "iteration_count": state.get("iteration_count", 0) + 1,
                "answer_metadata": {
                    "error": str(e)
                }
            }