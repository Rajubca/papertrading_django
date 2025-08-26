import os
import logging
from decimal import Decimal

log = logging.getLogger(__name__)

try:
    # Adjust import to your installed SDK package if different
    from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge

    _bridge = StocknoteAPIPythonBridge()
except Exception:
    _bridge = None
    log.warning('stocknotebridge SDK not available; ensure SDK is installed')

# If you have a SDK-specific session token/env, set it here:
SAMCO_SESSION_TOKEN = os.environ.get('SAMCO_SESSION_TOKEN')
if _bridge is not None and SAMCO_SESSION_TOKEN:
    try:
        _bridge.set_session_token(sessionToken=SAMCO_SESSION_TOKEN)
    except Exception:
        try:
            _bridge.set_session_token(SAMCO_SESSION_TOKEN)
        except Exception:
            log.debug('Unable to set session token on SDK bridge; check SDK API.')

from decimal import Decimal
from typing import Optional


def get_quote(symbol: str, exchange: str = 'NSE') -> Optional[Decimal]:
    # def get_quote(symbol: str, exchange: str = 'NSE') -> Decimal | None:
    symbol = symbol.strip().upper()
    try:
        if _bridge is not None:
            body = {'request': [{'exchange': exchange, 'tradingSymbol': symbol}]}
            resp = _bridge.quote(body=body)
            if isinstance(resp, dict):
                qd = resp.get('quoteDetails') or resp.get('data')
                if isinstance(qd, list) and qd:
                    first = qd[0]
                    for k in ('lastTradedPrice', 'ltp', 'lastPrice'):
                        if first.get(k) is not None:
                            return Decimal(str(first.get(k)))
                for k in ('ltp', 'lastTradedPrice', 'lastPrice'):
                    if resp.get(k) is not None:
                        return Decimal(str(resp.get(k)))
        # If SDK not available or parsing failed, return None (caller may fallback)
    except Exception:
        log.exception('get_quote failed for %s', symbol)
    return None


def multi_quote(symbols: list, exchange: str = 'NSE') -> dict:
    out = {}
    if not symbols:
        return out
    try:
        if _bridge is not None:
            body = {'request': [{'exchange': exchange, 'tradingSymbol': s.strip().upper()} for s in symbols]}
            # prefer multiQuote if present
            if hasattr(_bridge, 'multiQuote'):
                resp = _bridge.multiQuote(body=body)
            else:
                resp = _bridge.quote(body=body)
            if isinstance(resp, dict):
                qd = resp.get('quoteDetails') or resp.get('data')
                if isinstance(qd, list):
                    for item in qd:
                        sym = (item.get('tradingSymbol') or item.get('symbol') or '').upper()
                        for k in ('lastTradedPrice', 'ltp', 'lastPrice'):
                            if item.get(k) is not None:
                                out[sym] = Decimal(str(item.get(k)))
                                break
    except Exception:
        log.exception('multi_quote failed for %s', symbols)
    return out
