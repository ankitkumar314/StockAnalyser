# agents/planner.py

from datetime import datetime
from typing import Dict, Any

class PlannerAgent:
    """
    PlannerAgent: Analyzes and refines user queries for optimal semantic retrieval.
    
    This agent transforms raw user queries into optimized search queries by:
    - Identifying key concepts and entities
    - Expanding abbreviations and technical terms
    - Adding context for better semantic matching
    - Handling multi-part questions
    """

    def __init__(self, llm):
        self.llm = llm

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine the user's query for optimal semantic retrieval from vector store.
        
        Args:
            state: Current graph state containing the original query
            
        Returns:
            Dictionary with refined_query and query_analysis
        """
        try:
            original_query = state.get('query', '')
            iteration_count = state.get('iteration_count', 0)
            previous_feedback = state.get('feedback_on_work', '')
            messages = state.get('messages', [])
            previous_contexts = state.get('previous_contexts', [])
            memory = state.get('memory', {})
            
            system_message = f"""You are an expert query optimization specialist for earnings call transcript retrieval.
Your role is to transform user queries into optimized search queries that will retrieve the most relevant sections from quarterly/half-yearly earnings call transcripts stored in a vector database.

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Document Context:**
You are optimizing queries for earnings call transcripts (20-30+ pages) that contain:
- Management prepared remarks and presentations
- Q&A sessions between analysts and executives (CEO, CFO, etc.)
- Discussion of financial results, guidance, and business performance
- Forward-looking statements and strategic commentary
- Segment-specific performance discussions

**Your Responsibilities:**
1. Analyze the user's intent and identify what financial information they seek
2. Identify key financial concepts, metrics, and business terms
3. Expand abbreviations and financial acronyms (EBITDA, YoY, QoQ, etc.)
4. Add semantic context specific to earnings calls and financial discussions
5. Consider how management typically phrases guidance and commentary
6. Include synonyms for financial terms (e.g., "revenue" = "sales" = "top line")
7. Account for Q&A format where answers may be conversational

**Query Refinement Guidelines for Earnings Transcripts:**
- **For Guidance Questions**: Include terms like "outlook", "expect", "guidance", "forecast", "target", "projected"
- **For Performance Questions**: Add "quarter", "results", "performance", "growth", "compared to"
- **For Commentary**: Include "management said", "commentary", "discussed", "mentioned", "explained"
- **For Metrics**: Expand to include related terms (e.g., "margins" → "operating margin", "gross margin", "EBITDA margin")
- **For Segments**: Include business unit names, product lines, geographic regions
- **For Challenges/Risks**: Add "headwinds", "challenges", "concerns", "risks", "pressure"
- **For Strategy**: Include "initiatives", "plans", "strategy", "focus areas", "priorities"
- **For Executive Attribution**: Add role titles if asking about specific people (CEO, CFO, COO)

**Financial Term Expansion Examples:**
- "Revenue" → "revenue sales top line growth year-over-year quarter-over-quarter"
- "Profit" → "profit earnings net income bottom line profitability margins"
- "Guidance" → "guidance outlook forecast expectations targets projections full year"
- "Performance" → "performance results quarter quarterly half-yearly growth trends"

**Query Structure Tips:**
- Keep the core intent of the original query
- Add contextual keywords that executives use in earnings calls
- Use natural, conversational language (how people speak in Q&A)
- For multi-part questions, ensure all aspects are covered
- Include time-related terms (current quarter, next quarter, full year, etc.)
- Don't over-complicate simple, direct questions

**Output Format:**
Provide ONLY the refined query as a clear, natural language statement.
Do not include explanations, metadata, or formatting - just the optimized query text.
"""

            user_message = f"""Original Query: {original_query}

Task: Refine this query for optimal semantic retrieval from a document vector store.
"""

            if iteration_count > 0 and previous_feedback:
                user_message += f"""

**Previous Attempt Feedback:**
This is iteration {iteration_count + 1}. The previous refined query did not retrieve sufficient information.
Feedback: {previous_feedback}

Please create an improved refined query that addresses this feedback and uses different keywords or phrasing to find relevant documents.
"""
            
            if messages:
                conversation_context = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in messages[-5:]])
                user_message += f"""

**Recent Conversation Context:**
{conversation_context}

Use this context to better understand the user's intent and refine the query accordingly.
"""
            
            if memory and memory.get('learned_keywords'):
                user_message += f"""

**Learned Keywords from Previous Iterations:**
{', '.join(memory.get('learned_keywords', []))}

Consider incorporating relevant keywords that worked well before.
"""

            full_prompt = f"{system_message}\n\n{user_message}"
            
            if messages:
                from langchain.schema import SystemMessage, HumanMessage
                message_list = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=user_message)
                ]
                response = self.llm.invoke(message_list)
            else:
                response = self.llm.invoke(full_prompt)
            
            refined_query = response.content.strip()
            
            if not refined_query:
                refined_query = original_query
            
            updated_messages = messages + [{
                "role": "system",
                "content": system_message
            }, {
                "role": "user",
                "content": user_message
            }, {
                "role": "assistant",
                "content": refined_query
            }]
            
            return {
                "refined_query": refined_query,
                "query_analysis": f"Query refined from '{original_query}' to '{refined_query}'",
                "messages": updated_messages
            }
            
        except Exception as e:
            return {
                "refined_query": state.get('query', ''),
                "query_analysis": f"Error in query refinement: {str(e)}. Using original query."
            }