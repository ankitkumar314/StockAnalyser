import os
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse
from kiteconnect import KiteConnect

from app.services.kite_token_store import KiteTokenStore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["kite-auth"])


def _page(body: str, status_code: int = 200) -> HTMLResponse:
    return HTMLResponse(
        f'<div style="font-family: sans-serif; max-width: 640px; margin: 4rem auto;">{body}</div>',
        status_code=status_code,
    )


@router.get("/kite/login")
def kite_login():
    """Redirect the browser straight to the Zerodha login page for this app."""
    api_key = os.getenv("KITE_API_KEY")
    if not api_key:
        return _page("<h3>KITE_API_KEY is not set in .env</h3>", status_code=500)
    return RedirectResponse(KiteConnect(api_key=api_key).login_url())


@router.get("/redirect/zerodha", response_class=HTMLResponse)
def zerodha_redirect(request_token: Optional[str] = None, status: Optional[str] = None):
    """
    Kite Connect login redirect. If KITE_API_SECRET is configured, completes the
    session exchange server-side (generate_session) and stores the day's access
    token — no manual copy-paste. Otherwise falls back to displaying the
    request_token for use with scripts/generate_kite_access_token.py.
    """
    if not request_token:
        return _page(
            "<h3>No request_token in URL</h3>"
            f"<p>Login status: {status or 'unknown'}. Retry via <a href='/kite/login'>/kite/login</a>.</p>",
            status_code=400,
        )

    api_key = os.getenv("KITE_API_KEY")
    api_secret = os.getenv("KITE_API_SECRET")

    if not api_secret:
        return _page(f"""
            <h3>Zerodha login successful</h3>
            <p>KITE_API_SECRET is not set, so the token exchange must be done manually.
            Your <b>request_token</b> (valid a few minutes, single use):</p>
            <pre style="background:#f4f4f4; padding:1rem; font-size:1.1rem;">{request_token}</pre>
            <p>Paste it into <code>python scripts/generate_kite_access_token.py</code>,
            put the printed token in <code>.env</code> and restart. Or set
            <code>KITE_API_SECRET</code> in <code>.env</code> to make this automatic.</p>
        """)

    try:
        kite = KiteConnect(api_key=api_key)
        session = kite.generate_session(request_token, api_secret=api_secret)
        access_token = session["access_token"]
        KiteTokenStore.set_token(access_token)
        logger.info("Kite session established via /redirect/zerodha")

        return _page(f"""
            <h3>✅ Zerodha connected</h3>
            <p>Access token <code>{access_token[:4]}…{access_token[-4:]}</code> stored.
            It is active immediately — no server restart needed — and expires ~6 AM IST tomorrow.</p>
            <p>Try <a href="/portfolio">/portfolio</a> or <a href="/portfolio/analysis">/portfolio/analysis</a>.</p>
        """)

    except Exception as e:
        logger.error(f"Kite session exchange failed: {str(e)}")
        return _page(
            "<h3>Session exchange failed</h3>"
            f"<p>{str(e)}</p>"
            "<p>The request_token may have expired (they last only a few minutes) — "
            "retry via <a href='/kite/login'>/kite/login</a>. Also verify KITE_API_SECRET matches this api_key.</p>",
            status_code=502,
        )
