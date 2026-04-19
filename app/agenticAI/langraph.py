# graph/rag_graph.py

from langgraph.graph import StateGraph, END
from app.agenticAI.states import GraphState
from datetime import datetime

class RAGGraph:

    @staticmethod
    def evaluator_router(state: GraphState):
        # Stop if answer is correct
        if state["is_answer_correct"]:
            return "end"
    
        # Stop if max iterations reached
        if state["iteration_count"] >= state["max_iterations"]:
            return "end"
    
        # If not sufficient → retry retrieval
        if not state["is_sufficient"]:
            return "retriever"
    
        # Otherwise refine and retry
        return "planner"

    def __init__(self, planner, retriever, answerer, evaluator):
        self.builder = StateGraph(GraphState)

        self.builder.add_node("planner", planner.run)
        self.builder.add_node("retriever", retriever.run)
        self.builder.add_node("answerer", answerer.run)
        self.builder.add_node("evaluator", evaluator.run)

        self.builder.set_entry_point("planner")

        self.builder.add_edge("planner", "retriever")
        self.builder.add_edge("retriever", "answerer")
        self.builder.add_edge("answerer", "evaluator")

        self.builder.add_conditional_edges(
        "evaluator",
        RAGGraph.evaluator_router,
        {
            "retriever": "retriever",
            "planner": "planner",
            "end": END
        }
        )   

    def save_graph_visualization(self, filename="static/graph1.png"):
        try:
            compiled_graph = self.builder.compile()
            png_data = compiled_graph.get_graph().draw_mermaid_png()
            filename = f"static/{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, "wb") as f:
                f.write(png_data)
            print(f"Graph visualization generated and saved to {filename}")
        except Exception as e:
            print(f"Could not save graph: {e}")

    def compile(self):
        return self.builder.compile()