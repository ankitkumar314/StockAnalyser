# 📊 Conference Call Transcript Analysis System

## Overview

A comprehensive system for managing conference call transcripts with automated AI-powered summary generation using the existing RAG (Retrieval-Augmented Generation) system.

## 🏗️ Architecture

### Database Schema

#### 1. `conference_call_transcripts` Table
Stores raw transcript data with quarter-based deduplication.

```sql
CREATE TABLE conference_call_transcripts (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at        TIMESTAMP DEFAULT NOW(),
  updated_at        TIMESTAMP DEFAULT NOW(),
  stockId           INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
  quarter_date      DATE NOT NULL,
  transcript_url    VARCHAR,
  transcript_text   TEXT,
  doc_id            VARCHAR,  -- RAG system document ID
  status            VARCHAR DEFAULT 'pending',  -- pending, processing, completed, failed
  summary_id        INTEGER REFERENCES transcript_summaries(id) ON DELETE SET NULL
);

CREATE INDEX idx_transcript_stockId ON conference_call_transcripts(stockId);
CREATE INDEX idx_transcript_quarter ON conference_call_transcripts(quarter_date);
CREATE INDEX idx_transcript_status ON conference_call_transcripts(status);
```

#### 2. `transcript_summaries` Table
Stores AI-generated structured summaries.

```sql
CREATE TABLE transcript_summaries (
  id                      INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at              TIMESTAMP DEFAULT NOW(),
  stockId                 INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
  quarter_date            DATE NOT NULL,
  management_guidance     TEXT,
  key_metrics             JSONB,
  sentiment_analysis      JSONB,
  risks_and_challenges    TEXT,
  opportunities           TEXT,
  full_summary            TEXT
);

CREATE INDEX idx_summary_stockId ON transcript_summaries(stockId);
CREATE INDEX idx_summary_quarter ON transcript_summaries(quarter_date);
```

### Relationships

```
stocks (1) ──────< (N) conference_call_transcripts
  │                       │
  │                       └─ summary_id ──> transcript_summaries
  │
  └──────< (N) transcript_summaries
```

## 🔄 Complete Workflow

### Step 1: Extract Concall Data from Scraper

When scraping financial data, concall URLs are extracted:

```python
# In scraper service
scrape_result = {
    "data": {...},
    "growth": {...},
    "concalls": [
        {"url": "https://example.com/q1-2024.pdf", "quarter": "Q1 2024"},
        {"url": "https://example.com/q2-2024.pdf", "quarter": "Q2 2024"}
    ]
}
```

### Step 2: Create Transcript Records

For each concall URL, create a transcript record:

```bash
POST /transcripts
```

**Request:**
```json
{
  "ticker": "RELIANCE",
  "transcript_url": "https://example.com/q3-2024-concall.pdf",
  "quarter_date": "2024-09-30"  // Optional, auto-calculated if not provided
}
```

**Response:**
```json
{
  "id": 1,
  "stock_id": 1,
  "quarter_date": "2024-09-30",
  "transcript_url": "https://example.com/q3-2024-concall.pdf",
  "doc_id": null,
  "status": "pending",
  "summary_id": null,
  "created_at": "2024-04-20T10:15:30",
  "updated_at": "2024-04-20T10:15:30"
}
```

**Quarter-Based Deduplication:**
- Checks if transcript exists for same `(stockId, quarter_date)`
- If exists → Returns existing record
- If not → Creates new record with `status='pending'`

### Step 3: Generate Summary (Background Processing)

Trigger summary generation for a transcript:

```bash
POST /transcripts/generate-summary
```

**Request:**
```json
{
  "transcript_id": 1
}
```

**Response:**
```json
{
  "message": "Summary generation started",
  "transcript_id": 1,
  "status": "processing"
}
```

**Background Process:**

1. **Update Status** → `processing`

2. **Ingest PDF** (if `doc_id` is null)
   - Calls existing RAG system: `POST /agent/ingest-pdf`
   - Stores `doc_id` in transcript record

3. **Query RAG System** with predefined questions:
   - Management guidance for revenue, margins, outlook
   - Key revenue metrics and growth rates
   - Margin trends and profitability
   - Overall sentiment and management tone
   - Risks, challenges, and headwinds
   - Opportunities and growth drivers

4. **Extract Structured Summary**
   - Combines RAG responses into structured format
   - Stores in `transcript_summaries` table

5. **Update Transcript**
   - Links `summary_id` to transcript
   - Updates `status` → `completed`

### Step 4: Retrieve Summary

Get the latest summary for a ticker:

```bash
GET /transcripts/summary/{ticker}
```

**Response:**
```json
{
  "id": 1,
  "stock_id": 1,
  "quarter_date": "2024-09-30",
  "management_guidance": "Management expects Q4 revenue growth of 15-18% YoY...",
  "key_metrics": {
    "revenue_guidance": "...",
    "margin_trends": "...",
    "growth_metrics": "..."
  },
  "sentiment_analysis": {
    "overall_tone": "bullish",
    "confidence_level": "high"
  },
  "risks_and_challenges": "Supply chain constraints...",
  "opportunities": "Expanding into new markets...",
  "full_summary": "**Management Guidance:**\n...\n**Key Metrics:**\n...",
  "created_at": "2024-04-20T10:30:45"
}
```

## 📡 API Endpoints

### Transcript Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/transcripts` | POST | Create new transcript |
| `/transcripts/{id}` | GET | Get transcript by ID |
| `/transcripts/ticker/{ticker}` | GET | Get all transcripts for ticker |

### Summary Generation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/transcripts/generate-summary` | POST | Generate summary for transcript (background) |
| `/transcripts/summary/{ticker}` | GET | Get latest summary for ticker |
| `/transcripts/batch-process` | POST | Process pending transcripts in batch |

## 🔄 Batch Processing

Process multiple pending transcripts at once:

```bash
POST /transcripts/batch-process
```

**Request:**
```json
{
  "max_count": 10
}
```

**Response:**
```json
{
  "processed": 0,
  "success": 0,
  "failed": 0,
  "message": "Batch processing started for up to 10 transcripts"
}
```

**Use Case:**
- Run as a scheduled job (cron/celery)
- Process all pending transcripts automatically
- Ideal for overnight batch processing

## 🎯 Integration with Existing Scraper

Update the scraper to automatically create transcript records:

```python
# In webScrape_controller.py or scraper service
def scrape_for_financial_data(self, ticker: str):
    # ... existing scraping logic ...
    
    # Extract concall URLs from scrape result
    concalls = result.get('concalls', [])
    
    # Create transcript records for each concall
    for concall in concalls:
        TranscriptService.create_transcript(
            ticker=ticker,
            transcript_url=concall['url'],
            quarter_date=calculate_quarter_from_label(concall['quarter'])
        )
    
    return result
```

## 📊 Status Flow

```
pending → processing → completed
   │           │
   └───────────┴──────→ failed
```

- **pending**: Transcript created, waiting for summary generation
- **processing**: Summary generation in progress
- **completed**: Summary generated and linked
- **failed**: Summary generation failed (check logs)

## 🔍 Query Examples

### Get All Transcripts for a Stock
```bash
GET /transcripts/ticker/RELIANCE?limit=5
```

### Check Transcript Status
```bash
GET /transcripts/123
```

### Generate Summary
```bash
POST /transcripts/generate-summary
{
  "transcript_id": 123
}
```

### Get Latest Summary
```bash
GET /transcripts/summary/RELIANCE
```

## 🎨 Key Features

✅ **Quarter-Based Deduplication** - No duplicate transcripts for same quarter
✅ **Background Processing** - Non-blocking summary generation
✅ **Status Tracking** - Monitor progress of each transcript
✅ **Structured Summaries** - AI-extracted insights in organized format
✅ **Batch Processing** - Process multiple transcripts efficiently
✅ **RAG Integration** - Leverages existing AI system for analysis
✅ **Automatic Linking** - Transcripts linked to summaries via `summary_id`

## 🚀 Getting Started

1. **Create Stock** (if not exists)
   ```bash
   POST /stocks/db
   {
     "ticker": "RELIANCE",
     "stock_name": "Reliance Industries"
   }
   ```

2. **Create Transcript**
   ```bash
   POST /transcripts
   {
     "ticker": "RELIANCE",
     "transcript_url": "https://example.com/concall.pdf"
   }
   ```

3. **Generate Summary**
   ```bash
   POST /transcripts/generate-summary
   {
     "transcript_id": 1
   }
   ```

4. **Retrieve Summary**
   ```bash
   GET /transcripts/summary/RELIANCE
   ```

## 📝 Notes

- Quarter date is auto-calculated if not provided (based on current date)
- PDF ingestion happens automatically if `doc_id` is not present
- Summary generation runs in background using FastAPI BackgroundTasks
- Each transcript can have only one summary (1:1 relationship)
- Summaries are structured for easy consumption by frontend/analytics

## 🔧 Configuration

No additional configuration required! The system uses:
- Existing database connection
- Existing RAG system (AgentController)
- Existing PDF ingestion pipeline
- FastAPI background tasks (no Celery needed)

---

**Built with ❤️ for automated financial analysis**
