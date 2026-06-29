"""
CommerceMind VoiceCare AI — Short, human-readable IDs

Internal primary keys stay UUIDs; these short codes are what we read aloud to
the customer and show in the dashboard (e.g. "ORD-7K3F", "TKT-9QXM2").

The alphabet drops visually/aurally ambiguous characters (0/O, 1/I/L) so codes
are easy to convey over voice across languages and hard to mishear.
"""

import secrets
from typing import Callable, Optional

# No 0, O, 1, I, L — unambiguous when spoken or read.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def _random_code(prefix: str, length: int) -> str:
    body = "".join(secrets.choice(_ALPHABET) for _ in range(length))
    return f"{prefix}-{body}"


def generate_order_number(exists: Optional[Callable[[str], bool]] = None) -> str:
    """Generate an order number like 'ORD-7K3F'.

    If `exists(code)` is provided it is used to retry on collision; pass a
    callable that returns True when the code is already taken.
    """
    return _generate("ORD", 4, exists)


def generate_ticket_number(exists: Optional[Callable[[str], bool]] = None) -> str:
    """Generate a ticket number like 'TKT-9QXM2'."""
    return _generate("TKT", 5, exists)


def generate_customer_code(exists: Optional[Callable[[str], bool]] = None) -> str:
    """Generate a customer code like 'CUST-7K3F'."""
    return _generate("CUST", 4, exists)


def _generate(prefix: str, length: int, exists: Optional[Callable[[str], bool]]) -> str:
    for _ in range(10):
        code = _random_code(prefix, length)
        if exists is None or not exists(code):
            return code
    # Extremely unlikely; widen the space rather than fail.
    return _random_code(prefix, length + 2)
