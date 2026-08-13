"""
Offline report generator (v3) — stitch a research note together from JSON files
without needing the API server, database, Kite login or an LLM key.

Usage:
  python scripts/generate_offline_report.py \
      --holding sample_data/holding.json \
      --history sample_data/history.json \
      --scrape sample_data/scrape.json \
      --summary sample_data/concall_summary.json \
      --out reports/

File shapes (all optional except --holding):
  holding : one holding object from GET /portfolio (symbol, average_price, ...)
  history : GET /market-data/history response ({"bars": [...]}) or a bare list of bars
  scrape  : POST /scrape/get-financial-data response ({"data": {...}}) or the
            inner data dict itself (quarters / profit-loss / balance-sheet / ...)
  summary : POST /agent/batch-evaluate response ({"results": [{"answer": ...}]})
            or a bare list of answer strings
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.stock_report_service import StockReportService  # noqa: E402


def _load(path):
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Generate an offline stock research note")
    parser.add_argument("--holding", required=True)
    parser.add_argument("--history", default=None)
    parser.add_argument("--scrape", default=None)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()

    holding = _load(args.holding)

    history = _load(args.history)
    bars = history.get("bars") if isinstance(history, dict) else history

    scrape = _load(args.scrape)
    if isinstance(scrape, dict) and "data" in scrape:
        scrape = scrape["data"]

    summary = _load(args.summary)
    if isinstance(summary, dict) and "results" in summary:
        answers = [r["answer"] for r in summary["results"] if r.get("answer")]
    else:
        answers = summary

    report = StockReportService.build_report_data(
        holding, bars=bars, scrape_data=scrape, concall_answers=answers)
    markdown = StockReportService.render_markdown(report)

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, f"{holding['symbol']}_offline_report.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Report written to {out_path}")
    print(f"Composite score: {report['scorecard']['composite_score']} "
          f"— {report['scorecard']['stance']}")


if __name__ == "__main__":
    main()
