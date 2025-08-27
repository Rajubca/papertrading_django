# signals/utils.py
import re
_ALLOWED = re.compile(r"[^A-Za-z0-9_.-]")  # only alnum, underscore, dot, hyphen

def sanitize_group(name: str, maxlen: int = 95) -> str:
    clean = _ALLOWED.sub("-", (name or ""))
    return clean[:maxlen]

def group_all() -> str:
    return sanitize_group("signals.all")

def group_for_symbol(symbol: str) -> str:
    return sanitize_group(f"signals.symbol.{(symbol or '').upper()}")
