import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Kite access tokens expire daily, so a full DB table is overkill — a local
# file (gitignored, 0600) lets the token survive server restarts within the day.
_TOKEN_FILE = Path(__file__).resolve().parents[2] / ".kite_access_token"


class KiteTokenStore:
    """Holds the day's Kite access token: in-memory first, then the local token
    file, then the KITE_ACCESS_TOKEN env var as a manual fallback."""

    _token: Optional[str] = None

    @classmethod
    def set_token(cls, token: str) -> None:
        cls._token = token
        try:
            _TOKEN_FILE.write_text(token)
            _TOKEN_FILE.chmod(0o600)
            logger.info("Kite access token stored (in-memory + token file)")
        except Exception as e:
            logger.error(f"Could not persist Kite token file: {str(e)}")

    @classmethod
    def get_token(cls) -> Optional[str]:
        if cls._token:
            return cls._token

        try:
            if _TOKEN_FILE.exists():
                token = _TOKEN_FILE.read_text().strip()
                if token:
                    cls._token = token
                    return token
        except Exception as e:
            logger.error(f"Could not read Kite token file: {str(e)}")

        return os.getenv("KITE_ACCESS_TOKEN")

    @classmethod
    def clear(cls) -> None:
        cls._token = None
        try:
            _TOKEN_FILE.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Could not delete Kite token file: {str(e)}")
