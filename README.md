# 📊 Stock Analyser - AI-Powered Earnings Call Analysis System

An intelligent RAG (Retrieval-Augmented Generation) system built with FastAPI and LangGraph for analyzing quarterly/half-yearly earnings call transcripts. The system uses a multi-agent architecture to extract actionable insights from financial documents, providing management guidance, sentiment analysis, and business performance commentary.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.7-orange.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.45-red.svg)](https://langchain-ai.github.io/langgraph/)

## 🎯 Key Features

- **🤖 Multi-Agent RAG System**: Specialized agents for planning, retrieval, answering, and evaluation
- **📄 PDF Ingestion**: Automated processing of earnings call transcripts (20-30+ pages)
- **💡 Insight Extraction**: Extracts management guidance, sentiment, and strategic commentary
- **🔍 Semantic Search**: FAISS vector store with HuggingFace embeddings for precise retrieval
- **💰 Cost Tracking**: Real-time LLM cost monitoring and prediction
- **📊 LangSmith Integration**: Full observability and tracing for debugging
- **🌐 Web Scraping**: Financial data extraction from company websites
- **⚡ Async Processing**: High-performance FastAPI backend

## 🏗️ Architecture

### Agentic RAG Workflow

```
┌─────────────┐
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Planner Agent   │ ◄─── Refines query for optimal retrieval
└────────┬────────┘      (Financial term expansion, context awareness)
         │
         ▼
┌─────────────────┐
│ Retriever Agent │ ◄─── Semantic search in vector DB
└────────┬────────┘      (FAISS + HuggingFace embeddings)
         │
         ▼
┌─────────────────┐
│ Answer Agent    │ ◄─── Generates insights from context
└────────┬────────┘      (Management guidance, sentiment, metrics)
         │
         ▼
┌─────────────────┐
│ Evaluator Agent │ ◄─── Quality check & iteration control
└────────┬────────┘      (Grounded, Insightful, Useful)
         │
         ├─── ✅ Correct → Final Answer
         │
         └─── ❌ Insufficient → Loop back (max 3 iterations)
```

### Agent Responsibilities

| Agent | Purpose | Key Functions |
|-------|---------|---------------|
| **Planner** | Query optimization for earnings transcripts | Financial term expansion, synonym mapping, Q&A format awareness |
| **Retriever** | Semantic document retrieval | FAISS similarity search, conversation-based chunking |
| **Answerer** | Insight extraction & synthesis | Management guidance extraction, sentiment analysis, metric identification |
| **Evaluator** | Quality assurance | Checks for grounding, insights, usefulness, hallucinations |

## 📁 Project Structure

```
pythonCrud/
├── app/
│   ├── agenticAI/              # Core RAG system
│   │   ├── Agents/
│   │   │   ├── plannerAgent.py      # Query refinement for earnings calls
│   │   │   ├── retriverAgent.py     # Semantic search agent
│   │   │   ├── answerAgent.py       # Financial insight extraction
│   │   │   └── evaluatorAgent.py    # Answer quality evaluation
│   │   ├── vectorDB/
│   │   │   ├── main.py              # Vector DB manager
│   │   │   ├── documentIngestor.py  # PDF processing & chunking
│   │   │   └── vectorManager.py     # FAISS store management
│   │   ├── langraph.py              # LangGraph workflow orchestration
│   │   ├── llm_Model.py             # LLM factory (DeepSeek integration)
│   │   ├── cost_tracker.py          # Token usage & cost tracking
│   │   ├── langsmith_config.py      # LangSmith tracing setup
│   │   └── states.py                # Graph state definitions
│   ├── controllers/            # Business logic layer
│   │   ├── agent_controller.py      # RAG system endpoints
│   │   ├── stock_controller.py      # Stock data management
│   │   └── webScrape_controller.py  # Web scraping logic
│   ├── models/                 # Pydantic models
│   │   ├── agent.py                 # RAG request/response models
│   │   ├── stock.py                 # Stock data models
│   │   └── web_scrape.py            # Scraping models
│   ├── routes/                 # API endpoints
│   │   ├── agent_routes.py          # /agent/* endpoints
│   │   ├── stock_routes.py          # /stock/* endpoints
│   │   └── webScrape_routes.py      # /scrape/* endpoints
│   ├── services/               # Service layer
│   │   ├── webScrape_service.py     # Web scraping service
│   │   └── Scraper_service.py       # Financial data scraper
│   └── repositories/           # Data access layer
├── vectorstores/               # Persisted FAISS indexes
├── downloads/                  # Downloaded PDFs
├── static/                     # Graph visualizations
├── utility/                    # Helper functions
├── main.py                     # FastAPI application entry
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- DeepSeek API Key (or OpenAI-compatible LLM)
- LangSmith API Key (optional, for tracing)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ankitkumar314/StockAnalyser.git
cd StockAnalyser
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the root directory:

```env
# Required: LLM API Key
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_deepseek_api_key_here  # DeepSeek uses OpenAI-compatible API

# Optional: LangSmith Tracing (for debugging & monitoring)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=rag-agent-system
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

5. **Run the application**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, access interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Agent Endpoints (`/agent`)

#### 1. Ingest PDF Transcript
```bash
POST /agent/ingest-pdf
```

**Request:**
```json
{
  "pdf_url": "https://example.com/earnings-call-transcript.pdf"
}
```

**Response:**
```json
{
  "doc_id": "27bebce8-2659-4d78-a5ba-62a7750a85b4",
  "message": "PDF ingested successfully",
  "chunks_count": 45
}
```

#### 2. Query Earnings Transcript
```bash
POST /agent/query
```

**Request:**
```json
{
  "query": "What is the management guidance for next quarter revenue?",
  "doc_id": "27bebce8-2659-4d78-a5ba-62a7750a85b4"
}
```

**Response:**
```json
{
  "query": "What is the management guidance for next quarter revenue?",
  "answer": "### Key Insights\n- Management expects Q2 revenue to grow 15-18% YoY...",
  "doc_id": "27bebce8-2659-4d78-a5ba-62a7750a85b4"
}
```

#### 3. Batch Evaluation
```bash
POST /agent/batch-evaluate
```

Runs 6 predefined questions against the document for comprehensive analysis.

#### 4. Cost Tracking
```bash
GET /agent/cost-summary
GET /agent/cost-predict?query=...&doc_id=...
POST /agent/cost-reset
```

#### 5. Graph Visualization
```bash
GET /agent/graph-visualization
```

Generates a visual representation of the RAG workflow.

### Web Scraping Endpoints (`/scrape`)

```bash
POST /scrape/get-financial-data
POST /scrape
GET /scrape
GET /scrape/{url:path}
DELETE /scrape/{url:path}
```

## 🧠 How It Works

### 1. Document Ingestion

```python
# PDF is downloaded and processed
1. Download PDF from URL
2. Extract text using PyPDF
3. Split into conversation blocks (Q&A pairs)
4. Generate embeddings (BAAI/bge-large-en)
5. Store in FAISS vector database
6. Return unique doc_id
```

### 2. Query Processing

```python
# Multi-agent workflow
1. Planner: Refines query with financial terminology
   - "revenue" → "revenue sales top line growth YoY QoQ"
   
2. Retriever: Semantic search in vector DB
   - Finds relevant Q&A exchanges
   
3. Answerer: Extracts insights from context
   - Management guidance
   - Sentiment analysis
   - Key metrics
   
4. Evaluator: Quality check
   - Grounded in transcript?
   - Insightful?
   - Useful for investors?
   
5. Loop if needed (max 3 iterations)
```

### 3. Specialized for Earnings Calls

The system is optimized for financial transcripts:

- **Q&A Format Awareness**: Understands moderator, analyst, and executive exchanges
- **Financial Term Expansion**: Automatically expands acronyms (EBITDA, YoY, QoQ)
- **Management Attribution**: Identifies who said what (CEO, CFO, etc.)
- **Sentiment Capture**: Extracts management tone (bullish, cautious, confident)
- **Partial Data Handling**: Provides insights even from incomplete excerpts

## 💰 Cost Tracking

The system tracks LLM usage and costs in real-time:

```python
# Pricing (per 1M tokens)
DeepSeek Chat:     $0.14 input / $0.28 output
DeepSeek Reasoner: $0.55 input / $2.19 output
Cache Hit:         $0.014
```

**Example Cost Summary:**
```json
{
  "total_runs": 15,
  "total_tokens": {
    "input": 45000,
    "output": 12000,
    "total": 57000
  },
  "total_cost": 0.009540,
  "average_cost_per_run": 0.000636
}
```

## 🔧 Configuration

### LLM Models

The system uses DeepSeek models by default:
- **Planner & Answerer**: `deepseek-chat` (faster, cheaper)
- **Evaluator**: `deepseek-reasoner` (more thorough)

### Vector Store

- **Embedding Model**: `BAAI/bge-large-en` (1024 dimensions)
- **Vector DB**: FAISS (CPU version)
- **Chunk Strategy**: Conversation-based (Q&A pairs)

### Evaluation Criteria

The evaluator checks for:
- ✅ **Grounded**: All statements traceable to transcript
- ✅ **Insightful**: Extracts meaningful insights
- ✅ **Useful**: Helps investors/analysts
- ❌ **Hallucination**: No fabricated information
- 📊 **Coverage**: LOW/MEDIUM/HIGH context usage

## 🛠️ Development

### Running Tests

```bash
# Run the application
uvicorn main:app --reload --port 8000

# Test ingestion
curl -X POST "http://localhost:8000/agent/ingest-pdf" \
  -H "Content-Type: application/json" \
  -d '{"pdf_url": "https://example.com/transcript.pdf"}'

# Test query
curl -X POST "http://localhost:8000/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the revenue guidance?", "doc_id": "your-doc-id"}'
```

### Debugging with LangSmith

Enable tracing in `.env`:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
```

View traces at: https://smith.langchain.com/

## 📊 Example Use Cases

### 1. Extract Revenue Guidance
```
Query: "What is the management guidance for revenue growth?"

Answer:
### Key Insights
- Management expects Q2 revenue growth of 15-18% YoY
- Full year guidance raised to $2.5-2.7B (from $2.3-2.5B)

### Management Sentiment
- CEO expressed confidence in demand trends
- CFO noted strong pipeline visibility

### Supporting Evidence
- "We're seeing accelerating momentum across all segments" - CEO
- "Based on current trends, we feel comfortable raising guidance" - CFO
```

### 2. Analyze Margin Trends
```
Query: "What did management say about margins?"

Answer:
### Key Insights
- Operating margin expanded 200 bps to 18.5%
- Expect further improvement to 19-20% by year-end

### Management Commentary
- Cost optimization initiatives driving efficiency
- Scale benefits from revenue growth
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **LangChain** - RAG framework
- **LangGraph** - Multi-agent orchestration
- **FastAPI** - Web framework
- **DeepSeek** - LLM provider
- **FAISS** - Vector similarity search
- **HuggingFace** - Embedding models

## 📧 Contact

Ankit Kumar - [@ankitkumar314](https://github.com/ankitkumar314)

Project Link: [https://github.com/ankitkumar314/StockAnalyser](https://github.com/ankitkumar314/StockAnalyser)

---

**Built with ❤️ for financial analysts and investors**
