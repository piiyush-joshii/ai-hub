import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[3]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from shared.groq_client import call_groq  # noqa: E402

MAX_CONTRACT_CHARS = 15000


def trim_contract(text: str) -> str:
    if len(text) <= MAX_CONTRACT_CHARS:
        return text
    return text[:MAX_CONTRACT_CHARS] + "\n\n[... truncated for context limit ...]"
