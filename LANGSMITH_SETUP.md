# LangSmith Integration Guide

This document explains how to set up and use LangSmith for tracing, monitoring, and cost analysis in the RAG Agent System.

## Overview

LangSmith provides:
- **Trace Capture**: Visualize LLM calls and agent workflows
- **Performance Monitoring**: Track latency, token usage, and errors
- **Cost Analysis**: Real-time cost tracking and prediction
- **Debugging**: Detailed logs of all LLM interactions

## Setup Instructions

### 1. Get LangSmith API Key

1. Go to [https://smith.langchain.com/](https://smith.langchain.com/)
2. Sign up or log in
3. Navigate to Settings → API Keys
4. Create a new API key
5. Copy the API key

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=rag-agent-system
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

**Note**: LangSmith is optional. If not configured, the system will work normally without tracing.

### 3. Install Dependencies

```bash
pip install -r requiterment.txt
```

This includes:
- `langsmith>=0.1.0` - LangSmith SDK
- `langchain-callbacks-manager>=0.1.0` - Callback management

### 4. Verify Setup

Start your application and check the logs:

```bash
uvicorn main:app --reload
```

You should see:
```
INFO: LangSmith enabled for project: rag-agent-system
INFO: LangSmith tracing enabled for deepseek-reasoner
```

## Features

### 1. Automatic Trace Capture

Every LLM call is automatically traced when LangSmith is enabled:

- **Planner Agent**: Query refinement traces
- **Answer Agent**: Answer generation traces
- **Evaluator Agent**: Evaluation traces

View traces at: [https://smith.langchain.com/](https://smith.langchain.com/)

### 2. Cost Tracking

#### Get Cost Summary

```bash
GET /agent/cost-summary
```

**Response:**
```json
{
  "status": "success",
  "langsmith_enabled": true,
  "langsmith_project": "rag-agent-system",
  "total_runs": 15,
  "total_tokens": {
    "input": 12500,
    "output": 3200,
    "cache": 1500,
    "total": 15700
  },
  "total_cost": 0.008945,
  "average_cost_per_run": 0.000596,
  "runs": [...]
}
```

#### Predict Query Cost

```bash
GET /agent/cost-predict?query=What is the main topic?&doc_id=abc123
```

**Response:**
```json
{
  "status": "success",
  "query": "What is the main topic?",
  "doc_id": "abc123",
  "predictions": {
    "planner": {
      "model": "deepseek-reasoner",
      "estimated_tokens": {...},
      "predicted_cost": {
        "total": 0.000123
      }
    },
    "answerer": {...},
    "evaluator": {...}
  },
  "total_predicted_cost": 0.001456,
  "note": "This is an estimate. Actual costs may vary..."
}
```

#### Reset Cost Tracking

```bash
POST /agent/cost-reset
```

### 3. Cost Pricing

Current pricing (as of implementation):

**deepseek-reasoner:**
- Input: $0.55 / 1M tokens
- Output: $2.19 / 1M tokens
- Cache Hit: $0.014 / 1M tokens

**deepseek-chat:**
- Input: $0.14 / 1M tokens
- Output: $0.28 / 1M tokens
- Cache Hit: $0.014 / 1M tokens

## Usage Examples

### Example 1: Query with Tracing

```python
# Tracing is automatic when enabled
response = requests.post(
    "http://localhost:8000/agent/query",
    json={
        "query": "What are the key findings?",
        "doc_id": "doc_abc123"
    }
)

# View trace in LangSmith dashboard
# Check cost in /agent/cost-summary
```

### Example 2: Monitor Costs

```python
# Before running expensive batch operations
cost_prediction = requests.get(
    "http://localhost:8000/agent/cost-predict",
    params={
        "query": "Summarize the document",
        "doc_id": "doc_abc123"
    }
)

print(f"Estimated cost: ${cost_prediction['total_predicted_cost']}")

# Run the actual query
# ...

# Check actual cost
summary = requests.get("http://localhost:8000/agent/cost-summary")
print(f"Actual cost: ${summary['total_cost']}")
```

### Example 3: Batch Processing with Cost Tracking

```python
# Reset cost tracker before batch
requests.post("http://localhost:8000/agent/cost-reset")

# Run batch evaluation
response = requests.post(
    "http://localhost:8000/agent/batch-evaluate",
    json={"doc_id": "doc_abc123"}
)

# Get final cost summary
summary = requests.get("http://localhost:8000/agent/cost-summary")
print(f"Batch processing cost: ${summary['total_cost']}")
print(f"Total tokens: {summary['total_tokens']['total']}")
```

## Trace Analysis in LangSmith

### Viewing Traces

1. Go to [https://smith.langchain.com/](https://smith.langchain.com/)
2. Select your project: `rag-agent-system`
3. View traces with tags:
   - `rag` - All RAG operations
   - `query` - Single query operations
   - `batch` - Batch evaluations
   - `production` - Production queries

### Trace Details

Each trace shows:
- **Input/Output**: Full prompts and responses
- **Token Usage**: Input, output, and cache tokens
- **Latency**: Time taken for each step
- **Cost**: Calculated cost for the run
- **Metadata**: doc_id, query, agent type, etc.

### Filtering Traces

Use filters to analyze:
- Errors and failures
- High-cost queries
- Slow responses
- Specific document IDs

## Disabling LangSmith

To disable LangSmith tracing:

1. Set `LANGCHAIN_TRACING_V2=false` in `.env`
2. Or remove LangSmith environment variables
3. Cost tracking will still work locally

## Troubleshooting

### LangSmith Not Working

**Check:**
1. `LANGCHAIN_TRACING_V2=true` is set
2. `LANGCHAIN_API_KEY` is valid
3. Network connectivity to `api.smith.langchain.com`

**Logs:**
```
WARNING: LangSmith is disabled. Set LANGCHAIN_TRACING_V2=true...
```

### Cost Tracking Issues

**If costs show as 0:**
1. Check if LLM responses include `token_usage`
2. Verify pricing in `cost_tracker.py`
3. Check callback execution in logs

### Missing Traces

**If traces don't appear:**
1. Verify project name matches in LangSmith dashboard
2. Check API key permissions
3. Wait a few seconds for traces to sync

## Best Practices

1. **Use Tags**: Add meaningful tags for filtering
2. **Monitor Costs**: Check cost summary regularly
3. **Predict Before Batch**: Use cost prediction for large operations
4. **Reset Periodically**: Reset cost tracker for new sessions
5. **Review Traces**: Analyze failed queries in LangSmith

## API Reference

### Cost Tracking Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/cost-summary` | GET | Get cost and usage summary |
| `/agent/cost-predict` | GET | Predict cost for a query |
| `/agent/cost-reset` | POST | Reset cost tracking data |

### LangSmith Configuration

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `LANGCHAIN_TRACING_V2` | No | false | Enable tracing |
| `LANGCHAIN_API_KEY` | Yes* | - | LangSmith API key |
| `LANGCHAIN_PROJECT` | No | rag-agent-system | Project name |
| `LANGCHAIN_ENDPOINT` | No | https://api.smith.langchain.com | API endpoint |

*Required only if tracing is enabled

## Support

For issues or questions:
- LangSmith Docs: [https://docs.smith.langchain.com/](https://docs.smith.langchain.com/)
- LangChain Discord: [https://discord.gg/langchain](https://discord.gg/langchain)
