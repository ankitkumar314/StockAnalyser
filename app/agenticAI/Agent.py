# main.py

from llm_Model import LLMFactory
from Agents.plannerAgent import PlannerAgent
from Agents.retriverAgent import RetrieverAgent
from Agents.answerAgent import AnswerAgent
from Agents.evaluatorAgent import EvaluatorAgent
from langraph import RAGGraph

from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from app.agenticAI.vectorDB.main import VectorDBManager

# ---------------------------
# Setup
# ---------------------------
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en")
vector_db_manager = VectorDBManager()

# Assume vectorstore already built
doc_id = "your-doc-id-here"  # Get this from the ingest response

vectorstore = vector_db_manager.load_vector_store(doc_id)


planner = PlannerAgent(LLMFactory.get_deepseek())
retriever = RetrieverAgent(vectorstore)
answerer = AnswerAgent(LLMFactory.get_deepseek())
evaluator = EvaluatorAgent(LLMFactory.get_evaluator_model())

graph = RAGGraph(planner, retriever, answerer, evaluator).compile()

# ---------------------------
# Run
# ---------------------------
result = graph.invoke({
    "query": "Explain the key idea of the document"
})

print(result["final_answer"])