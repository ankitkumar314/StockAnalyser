# graph/state.py

from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict, total=False):
    query: str
    refined_query: str
    query_analysis: str
    documents: List
    context: List
    answer: str
    evaluation: str
    iteration_count: int
    max_iterations: int
    is_answer_correct: bool
    final_answer: str
    is_sufficient: bool
    feedback_on_work: str
    retrieval_metadata: Dict[str, Any]
    answer_metadata: Dict[str, Any]
    evaluation_metadata: Dict[str, Any]
    messages: List[Dict[str, str]]
    conversation_history: List[Dict[str, Any]]
    previous_contexts: List[List[Any]]
    previous_answers: List[str]
    memory: Dict[str, Any]