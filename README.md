# 📊 Stock Analyser - AI-Powered Financial Analysis & Data Platform

A comprehensive financial analysis platform combining AI-powered earnings call analysis with automated stock data scraping, live market data, and read-only Zerodha Kite portfolio integration. Built with FastAPI, LangGraph, and PostgreSQL, the system provides intelligent insights from earnings transcripts, caches them persistently, and turns them into an AI-written view of your own portfolio.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.7-orange.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.45-red.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)

## 🎯 Key Features

### AI-Powered Analysis
- **🤖 Multi-Agent RAG System**: Specialized agents for planning, retrieval, answering, and evaluation
- **📄 PDF Ingestion**: Automated processing of earnings call transcripts (20-30+ pages)
- **💡 Insight Extraction**: Extracts management guidance, sentiment, and strategic commentary
- **🔍 Semantic Search**: FAISS vector store with HuggingFace embeddings for precise retrieval
- **💰 Cost Tracking**: Real-time LLM cost monitoring and prediction
- **📊 LangSmith Integration**: Full observability and tracing for debugging

### Stock Data Management
- **🗄️ PostgreSQL Persistence**: Robust database storage for stock and financial data
- **🌐 Automated Web Scraping**: Real-time financial data extraction from screener websites
- **📈 Quarterly Data Tracking**: Smart quarter-based data storage with automatic updates
- **🔄 Duplicate Prevention**: Intelligent upsert logic - updates existing quarter data instead of creating duplicates
- **📊 Financial Metrics Storage**: JSONB columns for flexible storage of quarter results, growth metrics, and P&L data
- **⚡ Repository Pattern**: Clean separation of concerns with service and repository layers

### Portfolio & Market Data (v2)
- **💼 Zerodha Kite Integration (Read-Only)**: Fetch live portfolio holdings with P&L, concentration and totals
- **🔐 Kite Session Flow**: One-click daily login (`/kite/login`) with server-side token exchange — no manual token juggling
- **📈 Live Market Data**: Yahoo Finance quotes and historical OHLC via yfinance
- **🧠 Concall Summary Caching**: Batch-evaluate answers persisted to PostgreSQL — same document is never re-analysed twice
- **🤖 AI Portfolio Analysis**: LLM-written short view per holding + overall portfolio view, combining concall summaries and technical indicators

## 📦 Releases

### v1.0 — AI Concall Analysis & Data Platform
The foundation release:
- Multi-agent RAG system (Planner → Retriever → Answerer → Evaluator) over earnings-call PDFs
- PDF ingestion into FAISS vector stores with HuggingFace embeddings
- Single query (`/agent/query`) and 5-question batch evaluation (`/agent/batch-evaluate`)
- Stock master CRUD (`/stocks`) backed by PostgreSQL
- screener.in financial data scraping (`/scrape`) with quarter-based upsert persistence
- LLM cost tracking & prediction, LangSmith tracing

### v2.0 — Portfolio, Market Data & Persistent Summaries *(current)*
This release turns the platform from a document-analysis tool into a personal portfolio intelligence system:

| Feature | Endpoints | Notes |
|---|---|---|
| **Concall summary cache** | `POST /agent/batch-evaluate` | Answers now persisted to `concall_summary`; repeat calls for the same `doc_id` return instantly from DB (`cached: true`), saving minutes of LLM time and cost |
| **Live market data** | `GET /market-data/quote/{ticker}`, `GET /market-data/history/{ticker}` | Yahoo Finance via yfinance; Indian tickers need the exchange suffix (`KALYANKJIL.NS` / `.BO`) |
| **Kite portfolio (read-only)** | `GET /portfolio` | Holdings with invested/current value, P&L, P&L %, portfolio concentration — sorted by current value. Strictly no trading endpoints |
| **Kite session flow** | `GET /kite/login`, `GET /redirect/zerodha` | Official Kite Connect login → request_token → `generate_session` exchange done server-side; day's access token stored (memory + gitignored file), effective without restart |
| **AI portfolio analysis (preview)** | `GET /portfolio/analysis` | Per-holding LLM short view + overall portfolio view from cached concall summaries and technical indicators (indicators are **dummy placeholders** in v2) |
| **Unit tests** | `tests/` | Portfolio calculation math and transcript-URL picking covered by pytest |

### v3.0 — Full Portfolio Intelligence *(planned)*
- **Real technical analysis**: actual MACD, 50/200 DMA and DMA crossover computed from yfinance OHLC history (replacing the v2 dummy indicator service)
- **Full-auto portfolio pipeline**: every holding automatically scraped → latest concall ingested → summarised → cached, end to end
- **Combined technical + fundamental view**: one report per holding merging concall insights, technical signals, and quarterly financials from scrape data
- **Portfolio-level risk view**: concentration, sector exposure, and signal-based watchlist across all holdings

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
│   │   ├── stock_controller.py      # Stock CRUD operations
│   │   ├── webScrape_controller.py  # Web scraping & data persistence
│   │   ├── market_data_controller.py       # (v2) Live quotes & history
│   │   ├── portfolio_controller.py         # (v2) Kite holdings
│   │   └── portfolio_analysis_controller.py # (v2) AI portfolio analysis
│   ├── database/               # Database layer
│   │   ├── connection.py            # PostgreSQL connection manager
│   │   ├── models.py                # SQLAlchemy ORM models
│   │   ├── stock_repository.py      # Stock data repository
│   │   ├── stock_scrap_data_repository.py  # Financial data repository
│   │   └── summary_repository.py    # (v2) Concall summary cache repository
│   ├── models/                 # Pydantic models
│   │   ├── agent.py                 # RAG request/response models
│   │   ├── stock.py                 # Stock data models
│   │   ├── stock_scrape.py          # Stock scrape response models
│   │   ├── web_scrape.py            # Scraping models
│   │   ├── market_data.py           # (v2) Quote & OHLC models
│   │   ├── portfolio.py             # (v2) Portfolio holding models
│   │   └── portfolio_analysis.py    # (v2) Analysis response models
│   ├── routes/                 # API endpoints
│   │   ├── agent_routes.py          # /agent/* endpoints
│   │   ├── stock_routes.py          # /stocks/* endpoints
│   │   ├── webScrape_routes.py      # /scrape/* endpoints
│   │   ├── market_data_routes.py    # (v2) /market-data/* endpoints
│   │   ├── portfolio_routes.py      # (v2) /portfolio endpoint
│   │   ├── portfolio_analysis_routes.py  # (v2) /portfolio/analysis
│   │   └── kite_redirect_routes.py  # (v2) /kite/login + /redirect/zerodha
│   ├── services/               # Service layer
│   │   ├── webScrape_service.py     # Web scraping service
│   │   ├── Scraper_service.py       # Financial data scraper
│   │   ├── stock_scrape_data_service.py  # Stock data persistence service
│   │   ├── summary_cache_service.py # (v2) Batch-evaluate answer caching
│   │   ├── market_data_service.py   # (v2) yfinance quotes & history
│   │   ├── kite_service.py          # (v2) Kite holdings + portfolio math
│   │   ├── kite_token_store.py      # (v2) Day's access token storage
│   │   ├── portfolio_analysis_service.py  # (v2) Analysis orchestrator
│   │   └── technicalIndicator_service.py  # (v2) Indicators (dummy, real in v3)
│   └── repositories/           # Legacy data access layer
├── scripts/
│   └── generate_kite_access_token.py  # (v2) Manual token fallback
├── tests/                      # (v2) pytest unit tests
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
- PostgreSQL 14+ (for stock data persistence)
- DeepSeek API Key (or OpenAI-compatible LLM)
- LangSmith API Key (optional, for tracing)
- Zerodha Kite Connect app — api_key + api_secret (optional, for portfolio endpoints)

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
# Required: Database Connection
DATABASE_URL=postgresql://username:password@localhost:5432/stockanalyser

# Required: LLM API Key
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_deepseek_api_key_here  # DeepSeek uses OpenAI-compatible API

# Optional: LangSmith Tracing (for debugging & monitoring)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=rag-agent-system
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Optional (v2): Zerodha Kite Connect - portfolio endpoints
# With the secret set, open http://localhost:8000/kite/login once a day;
# the app exchanges and stores the day's access token automatically.
KITE_API_KEY=your_kite_api_key_here
KITE_API_SECRET=your_kite_api_secret_here
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

#### 3. Batch Evaluation (with persistent caching — v2)
```bash
POST /agent/batch-evaluate
```

Runs 5 predefined questions against the document for comprehensive analysis.
Results are **persisted to the `concall_summary` table**; calling again with the
same `doc_id` returns instantly from the database with `"cached": true`.

**Request:**
```json
{
  "doc_id": "27bebce8-2659-4d78-a5ba-62a7750a85b4",
  "ticker": "KALYANKJIL",
  "quarter_date": "2026-06-30",
  "concall_url": "https://example.com/transcript.pdf"
}
```
`ticker`, `quarter_date` and `concall_url` are optional — when provided they link
the cached summary to the stock and quarter in the database.

**Response:**
```json
{
  "doc_id": "27bebce8-2659-4d78-a5ba-62a7750a85b4",
  "total_questions": 5,
  "results": [{"question": "...", "answer": "...", "iteration_count": 1}],
  "cached": false
}
```

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

### Stock Management Endpoints (`/stocks`)

#### 1. Create Stock
```bash
POST /stocks/db
```

**Request:**
```json
{
  "stock_name": "Reliance Industries",
  "ticker": "RELIANCE",
  "screener_link": "https://www.screener.in/company/RELIANCE/",
  "market_size": "Large Cap",
  "last_stock_price": 2450
}
```

**Response:**
```json
{
  "stock_name": "Reliance Industries",
  "ticker": "RELIANCE",
  "screener_link": "https://www.screener.in/company/RELIANCE/",
  "market_size": "Large Cap",
  "last_stock_price": 2450,
  "created_at": "2026-04-20T10:15:30",
  "update_at": "2026-04-20T10:15:30"
}
```

#### 2. Get Stock by Ticker
```bash
GET /stocks/db/ticker/{ticker}
```

#### 3. Get All Stocks
```bash
GET /stocks/db?limit=50&offset=0
```

#### 4. Update Stock
```bash
PUT /stocks/db/{stock_id}
```

#### 5. Delete Stock
```bash
DELETE /stocks/db/{stock_id}
```

### Web Scraping Endpoints (`/scrape`)

#### 1. Scrape Financial Data
```bash
POST /scrape/get-financial-data
```

**Request:**
```json
{
  "ticker": "RELIANCE"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "quarters": {...},
    "profit-loss": {...},
    "shareholding": {...}
  },
  "growth": {
    "sales": {...},
    "net_profit": {...},
    "operating_profit": {...}
  }
}
```

**Note:** This endpoint automatically:
- Scrapes financial data from the stock's screener link
- Stores/updates data in the `stock_scrape_data` table
- Uses quarter-based deduplication (updates existing quarter data)

#### 2. Get Latest Scraped Data
```bash
GET /scrape/{ticker}
```

**Response:**
```json
{
  "quarter_result": {...},
  "growth_sales": {...},
  "growth_net_profit": {...},
  "growth_operating_profit": {...},
  "shareholding_pattern": {...},
  "profit_loss": {...},
  "quarter_date": "2026-09-30",
  "created_at": "2026-04-20T10:15:30"
}
```

### Market Data Endpoints (`/market-data`) — v2

#### 1. Live Quote
```bash
GET /market-data/quote/{ticker}
```
Indian tickers need the Yahoo exchange suffix: `KALYANKJIL.NS` (NSE) or `KALYANKJIL.BO` (BSE).

**Response:**
```json
{
  "ticker": "KALYANKJIL.NS",
  "price": 574.4,
  "previous_close": 546.6,
  "day_change": 27.8,
  "day_change_percent": 5.08,
  "day_high": 577.5,
  "day_low": 541.25,
  "volume": 53915340,
  "market_cap": 593205985280,
  "currency": "INR",
  "fetched_at": "2026-07-18T18:52:43Z"
}
```

#### 2. Historical OHLC
```bash
GET /market-data/history/{ticker}?period=1mo&interval=1d
```
Returns OHLC bars (`date`, `open`, `high`, `low`, `close`, `volume`) for charting
or indicator calculations. `period`/`interval` accept standard yfinance values
(`5d`, `1mo`, `1y`, `1d`, `1wk`, ...).

> **Note:** Yahoo Finance is an unofficial data source with no published rate
> limits — keep request volume modest.

### Zerodha Kite Endpoints — v2 (Read-Only)

#### 1. Daily Login (once per day)
```bash
GET /kite/login          # open in a browser
```
Redirects to Zerodha's login page. After login, Zerodha redirects to
`/redirect/zerodha`, where the server completes the official Kite Connect
session exchange (`generate_session`) and stores the day's access token —
active immediately, no restart needed. Kite access tokens expire daily
(~6 AM IST), so this is a once-a-day step.

Requires `KITE_API_KEY` and `KITE_API_SECRET` in `.env`, and the app's redirect
URL in the [Kite developer console](https://developers.kite.trade/apps) set to
`http://localhost:8000/redirect/zerodha`.

#### 2. Portfolio Holdings
```bash
GET /portfolio
```

**Response:**
```json
{
  "portfolio_value": 1245634.50,
  "total_investment": 1123400.25,
  "total_pnl": 122234.25,
  "total_pnl_percent": 10.88,
  "holdings": [
    {
      "symbol": "RELIANCE",
      "company_name": "Reliance Industries Ltd",
      "exchange": "NSE",
      "quantity": 15,
      "average_price": 2475.50,
      "current_price": 2860.30,
      "invested_value": 37132.50,
      "current_value": 42904.50,
      "profit_loss": 5772.00,
      "profit_loss_percent": 15.54,
      "portfolio_concentration": 3.44
    }
  ]
}
```
Holdings are sorted by current value (largest first). Errors: `401` expired/invalid
token, `503` network failure, `502` other Zerodha API failures.

> **Strictly read-only** — no order placement, positions, margins, or any trading
> functionality is implemented.

#### 3. AI Portfolio Analysis (preview)
```bash
GET /portfolio/analysis?generate_missing=false&max_generate=2
```
Combines Kite holdings + cached concall summaries + technical indicators
(**dummy values in v2**) into an LLM-written 3-4 sentence view per holding and
an overall portfolio view.

- `generate_missing=true`: for holdings without a cached concall summary, runs
  the full scrape → ingest → batch-evaluate pipeline (slow — minutes per stock),
  capped by `max_generate`
- Response also lists `not_tracked` (holdings missing from the `stocks` table)
  and `missing_summaries` (holdings still needing summary generation)

## 🧠 How It Works

### 1. Document Ingestion (RAG System)

```python
# PDF is downloaded and processed
1. Download PDF from URL
2. Extract text using PyPDF
3. Split into conversation blocks (Q&A pairs)
4. Generate embeddings (BAAI/bge-large-en)
5. Store in FAISS vector database
6. Return unique doc_id
```

### 2. Query Processing (RAG System)

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

### 3. Stock Data Management Workflow

```python
# Automated financial data scraping and persistence
1. Create Stock Entry
   POST /stocks/db → Store stock metadata in PostgreSQL
   
2. Scrape Financial Data
   POST /scrape/get-financial-data?ticker=RELIANCE
   ├─ Fetch data from screener.in
   ├─ Extract quarter results, growth metrics, P&L
   └─ Calculate current quarter (Q1-Q4) from date
   
3. Smart Persistence (Upsert Logic)
   ├─ Check if data exists for current quarter
   ├─ If EXISTS → UPDATE existing record
   └─ If NOT EXISTS → CREATE new record
   
4. Retrieve Latest Data
   GET /scrape/{ticker} → Returns most recent quarter data
```

### 5. Specialized for Earnings Calls

The system is optimized for financial transcripts:

- **Q&A Format Awareness**: Understands moderator, analyst, and executive exchanges
- **Financial Term Expansion**: Automatically expands acronyms (EBITDA, YoY, QoQ)
- **Management Attribution**: Identifies who said what (CEO, CFO, etc.)
- **Sentiment Capture**: Extracts management tone (bullish, cautious, confident)
- **Partial Data Handling**: Provides insights even from incomplete excerpts

## 🗄️ Database Schema

### Tables

#### 1. `stocks` - Stock Master Data
#### 2. `stock_scrape_data` - Quarterly Financial Data
#### 3. `concall_summary` - Cached Batch-Evaluate Answers (v2)
Stores the 5 batch-evaluate answers per document (`answer1`..`answer5`), keyed by
`document_id`, optionally linked to a stock (`stockid`) and `quarter_date` — this
is the persistent cache behind `POST /agent/batch-evaluate` and the source of
concall insights for `GET /portfolio/analysis`.
#### 4. `concall_transcript` - Transcript Tracking

### Relationships

```
stocks (1) ──────< (N) stock_scrape_data
  │                       │
  │                       └─ Multiple quarterly records (one per quarter)
  │
  ├──────< (N) concall_summary      (cached AI answers per document/quarter)
  └──────< (N) concall_transcript   (transcript URLs + processing status)
```

### JSONB Column Structure

**quarter_result:**
```json
{
  "Q1 FY24": {"revenue": 50000, "profit": 5000},
  "Q2 FY24": {"revenue": 55000, "profit": 5500}
}
```

**growth_sales / growth_net_profit / growth_operating_profit:**
```json
{
  "YoY": "15%",
  "QoQ": "8%",
  "3Y_CAGR": "12%"
}
```

**shareholding_pattern:**
```json
{
  "promoter": 65.5,
  "institutional": 20.3,
  "retail": 14.2
}
```

**profit_loss:**
```json
{
  "revenue": 50000,
  "expenses": 40000,
  "net_profit": 5000,
  "margin": 10
}
```

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
# Unit tests (portfolio calculations, transcript URL picking)
python -m pytest tests/ -v

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
