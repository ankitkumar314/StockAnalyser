from app.services.portfolio_analysis_service import pick_latest_transcript_url


def test_pick_latest_transcript_url_returns_first_transcript():
    concalls = {
        "May 2026": [{"ppt": "https://x/ppt1.pdf", "transcript": "https://x/t1.pdf"}],
        "Feb 2026": [{"transcript": "https://x/t2.pdf"}],
    }
    assert pick_latest_transcript_url(concalls) == "https://x/t1.pdf"


def test_pick_latest_transcript_url_skips_entries_without_transcript():
    concalls = {
        "May 2026": [{"ppt": "https://x/ppt1.pdf", "rec": "https://x/rec1"}],
        "Feb 2026": [{"transcript": "https://x/t2.pdf"}],
    }
    assert pick_latest_transcript_url(concalls) == "https://x/t2.pdf"


def test_pick_latest_transcript_url_empty_or_none():
    assert pick_latest_transcript_url({}) is None
    assert pick_latest_transcript_url(None) is None
    assert pick_latest_transcript_url({"May 2026": [{"ppt": "https://x/p.pdf"}]}) is None
