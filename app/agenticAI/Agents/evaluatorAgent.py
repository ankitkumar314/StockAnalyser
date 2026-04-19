# agents/evaluator.py

from datetime import datetime
from typing import Dict, Any, List
import logging
import json
import re

logger = logging.getLogger(__name__)

class EvaluatorAgent:
    """
    EvaluatorAgent: Evaluates answer quality and determines next actions.
    
    This agent performs comprehensive evaluation by:
    - Assessing answer grounding in context documents
    - Detecting hallucinations and unsupported claims
    - Evaluating completeness and accuracy
    - Determining if retrieval was sufficient
    - Providing actionable feedback for improvement
    - Making routing decisions for the workflow
    """

    def __init__(self, llm):
        self.llm = llm

    def _format_context(self, docs: List[Any]) -> str:
        """
        Format context documents for evaluation.
        
        Args:
            docs: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not docs:
            return "No context documents available."
        
        return "\n\n".join([f"[Doc {i+1}] {doc.page_content}" for i, doc in enumerate(docs)])

    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM's evaluation response into structured data.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Dictionary with parsed evaluation results
        """
        try:
            is_grounded_match = re.search(r'GROUNDED:\s*(YES|NO)', response_text, re.IGNORECASE)
            is_insightful_match = re.search(r'INSIGHTFUL:\s*(YES|NO)', response_text, re.IGNORECASE)
            is_useful_match = re.search(r'USEFUL:\s*(YES|NO)', response_text, re.IGNORECASE)
            has_hallucination_match = re.search(r'HALLUCINATION:\s*(YES|NO)', response_text, re.IGNORECASE)
            coverage_match = re.search(r'COVERAGE:\s*(LOW|MEDIUM|HIGH)', response_text, re.IGNORECASE)
            
            is_grounded = is_grounded_match.group(1).upper() == 'YES' if is_grounded_match else False
            is_insightful = is_insightful_match.group(1).upper() == 'YES' if is_insightful_match else False
            is_useful = is_useful_match.group(1).upper() == 'YES' if is_useful_match else False
            has_hallucination = has_hallucination_match.group(1).upper() == 'YES' if has_hallucination_match else False
            coverage = coverage_match.group(1).upper() if coverage_match else "LOW"
            
            is_sufficient = coverage in ["MEDIUM", "HIGH"]
            
            feedback_match = re.search(r'FEEDBACK:\s*(.+?)(?=\n\n|IMPROVED_ANSWER:|$)', response_text, re.DOTALL | re.IGNORECASE)
            feedback = feedback_match.group(1).strip() if feedback_match else "No specific feedback provided."
            
            improved_answer_match = re.search(r'IMPROVED_ANSWER:\s*(.+)$', response_text, re.DOTALL | re.IGNORECASE)
            improved_answer = improved_answer_match.group(1).strip() if improved_answer_match else None
            
            is_answer_correct = (
                is_grounded
                and not has_hallucination
                and is_insightful
                and is_useful
                and coverage in ["MEDIUM", "HIGH"]
            )
            
            return {
                "is_grounded": is_grounded,
                "is_insightful": is_insightful,
                "is_useful": is_useful,
                "has_hallucination": has_hallucination,
                "coverage": coverage,
                "is_sufficient": is_sufficient,
                "is_answer_correct": is_answer_correct,
                "feedback": feedback,
                "improved_answer": improved_answer
            }
        except Exception as e:
            logger.error(f"Error parsing evaluation response: {str(e)}")
            return {
                "is_grounded": False,
                "is_insightful": False,
                "is_useful": False,
                "has_hallucination": True,
                "coverage": "LOW",
                "is_sufficient": False,
                "is_answer_correct": False,
                "feedback": f"Error parsing evaluation: {str(e)}",
                "improved_answer": None
            }

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the generated answer and determine next actions.
        
        Args:
            state: Current graph state with answer, context, and query
            
        Returns:
            Dictionary with evaluation results and routing decisions
        """
        try:
            context_docs = state.get("context", [])
            answer = state.get("answer", "")
            query = state.get("query", "")
            refined_query = state.get("refined_query", query)
            iteration_count = state.get("iteration_count", 0)
            retrieval_metadata = state.get("retrieval_metadata", {})
            messages = state.get("messages", [])
            previous_contexts = state.get("previous_contexts", [])
            previous_answers = state.get("previous_answers", [])
            memory = state.get("memory", {})
            
            context_text = self._format_context(context_docs)
            
            system_message = f"""
           You are an expert evaluator for financial insight extraction systems.

Your job is NOT to check for perfect completeness.
Your job is to evaluate whether the answer extracts useful insights from available context.

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Evaluation Criteria:**

1. **GROUNDING**: Is every claim in the answer supported by the context documents?
   - YES: All statements can be traced to specific context passages
   - NO: Contains information not present in the context

2. INSIGHTFUL:
- Does the answer extract meaningful insights (trends, sentiment, conclusions)?

3. **ACCURACY**: Are the facts and details correct based on the context?
   - YES: All facts match the context accurately
   - NO: Contains errors, misinterpretations, or distortions

4. **USEFUL**:
- Would this answer help an investor or analyst?


5. **HALLUCINATION**: Does the answer contain fabricated or assumed information?
   - YES: Contains made-up facts, assumptions, or external knowledge
   - NO: Strictly adheres to context information

6. **COVERAGE**:
- Does it use the available context well?

### Important Rules:
- DO NOT penalize missing data
- DO NOT expect full financial summaries
- REWARD partial but meaningful insights
- Penalize ONLY if:
  - hallucination
  - ignoring obvious insights
  - generic or useless answer

**Your Task:**
Evaluate the answer against these criteria and provide:
1. Assessment for each criterion (YES/NO)
2. Detailed feedback explaining your evaluation
3. If the answer is insufficient, provide an improved version OR suggest what's needed

**Output Format:**
GROUNDED: YES/NO
INSIGHTFUL: YES/NO
USEFUL: YES/NO
HALLUCINATION: YES/NO
COVERAGE: LOW/MEDIUM/HIGH

FEEDBACK:
[Your detailed feedback explaining the evaluation, what's good, what's missing, what needs improvement]

IMPROVED_ANSWER:
[If the answer is not correct, provide an improved version here. If the answer is good, write "APPROVED" here]
"""

            user_message = f"""**Original Question:**
{query}

**Refined Query Used:**
{refined_query}

**Context Documents Retrieved:**
{context_text}

**Answer to Evaluate:**
{answer}

**Retrieval Metadata:**
- Documents Retrieved: {retrieval_metadata.get('document_count', 0)}
- Retrieval Status: {retrieval_metadata.get('status', 'unknown')}
- Quality Assessment: {retrieval_metadata.get('assessment', 'unknown')}

**Current Iteration:** {iteration_count}

**Task:**
Evaluate this answer thoroughly using the criteria above. Provide your assessment in the specified format.
"""

            if iteration_count > 1:
                user_message += f"""

**Note:** This is iteration {iteration_count}. Previous attempts were rejected. Be thorough in your evaluation.
"""
            
            if previous_answers and len(previous_answers) > 1:
                user_message += f"""

**Previous Answer History:**
"""
                for idx, prev_ans in enumerate(previous_answers[-3:], 1):
                    user_message += f"""
Attempt {idx}: {prev_ans[:150]}{'...' if len(prev_ans) > 150 else ''}
"""
                user_message += """

Consider the pattern of improvements across iterations when evaluating.
"""
            
            if previous_contexts:
                total_docs_seen = sum(len(ctx) for ctx in previous_contexts)
                user_message += f"""

**Retrieval History:**
- Total iterations: {len(previous_contexts)}
- Total documents seen across all iterations: {total_docs_seen}
- Current documents: {len(context_docs)}

If retrieval is insufficient, consider whether we need different search terms or if the document base lacks the information.
"""

            full_prompt = f"{system_message}\n\n{user_message}"
            
            logger.info(f"Evaluating answer (iteration {iteration_count})")
            
            if messages:
                from langchain.schema import SystemMessage, HumanMessage
                message_list = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=user_message)
                ]
                response = self.llm.invoke(message_list)
            else:
                response = self.llm.invoke(full_prompt)
            
            evaluation_text = response.content
            
            parsed_eval = self._parse_evaluation_response(evaluation_text)
            
            final_answer = answer
            if parsed_eval["improved_answer"] and parsed_eval["improved_answer"] != "APPROVED":
                final_answer = parsed_eval["improved_answer"]
            
            logger.info(f"Evaluation complete - Correct: {parsed_eval['is_answer_correct']}, Sufficient: {parsed_eval['is_sufficient']}")
            
            updated_messages = messages + [{
                "role": "system",
                "content": system_message
            }, {
                "role": "user",
                "content": user_message
            }, {
                "role": "assistant",
                "content": evaluation_text
            }]
            
            updated_memory = memory.copy() if memory else {}
            
            if parsed_eval["is_answer_correct"]:
                if "successful_patterns" not in updated_memory:
                    updated_memory["successful_patterns"] = []
                updated_memory["successful_patterns"].append({
                    "iteration": iteration_count,
                    "answer_length": len(answer),
                    "docs_used": len(context_docs),
                    "query": refined_query
                })
                if "learned_keywords" not in updated_memory:
                    updated_memory["learned_keywords"] = []
                keywords = refined_query.split()[:5]
                updated_memory["learned_keywords"].extend(keywords)
                updated_memory["learned_keywords"] = list(set(updated_memory["learned_keywords"]))
            else:
                if "common_issues" not in updated_memory:
                    updated_memory["common_issues"] = []
                updated_memory["common_issues"].append({
                    "iteration": iteration_count,
                    "issue": parsed_eval["feedback"][:100],
                    "was_grounded": parsed_eval["is_grounded"],
                    "was_insightful": parsed_eval["is_insightful"],
                    "coverage": parsed_eval["coverage"]
                })
            
            return {
                "final_answer": final_answer,
                "is_answer_correct": parsed_eval["is_answer_correct"],
                "is_sufficient": parsed_eval["is_sufficient"],
                "feedback_on_work": parsed_eval["feedback"],
                "evaluation": evaluation_text,
                "messages": updated_messages,
                "memory": updated_memory,
                "evaluation_metadata": {
                    "is_grounded": parsed_eval["is_grounded"],
                    "is_insightful": parsed_eval["is_insightful"],
                    "is_useful": parsed_eval["is_useful"],
                    "has_hallucination": parsed_eval["has_hallucination"],
                    "coverage": parsed_eval["coverage"],
                    "iteration": iteration_count,
                    "total_iterations": len(previous_answers) if previous_answers else 0
                },
                "iteration_count": iteration_count
            }
            
        except Exception as e:
            logger.error(f"Error in evaluation: {str(e)}")
            return {
                "final_answer": state.get("answer", "Error in evaluation"),
                "is_answer_correct": False,
                "is_sufficient": True,
                "feedback_on_work": f"Evaluation error: {str(e)}",
                "evaluation": f"Error: {str(e)}",
                "evaluation_metadata": {
                    "error": str(e)
                },
                "iteration_count": state.get("iteration_count", 0)
            }