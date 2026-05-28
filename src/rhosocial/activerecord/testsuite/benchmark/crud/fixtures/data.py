"""Deterministic payloads for CRUD benchmark scenarios."""

from typing import Dict, List


SPECIAL_NOTES = [
    "plain text",
    " leading and trailing spaces ",
    "line\nbreak\tand tab",
    "unicode café 中文 русский عربى",
    "emoji 😀🚀",
    "quotes 'single' \"double\" backslash \\",
    "LIKE chars 100%_match",
    "' OR '1'='1",
    "; DROP TABLE users; --",
]


def make_user_payload(index: int) -> Dict[str, object]:
    note = SPECIAL_NOTES[index % len(SPECIAL_NOTES)]
    return {
        "username": f"bench_user_{index}",
        "email": f"bench_user_{index}@example.com",
        "age": 18 + (index % 83),
        "balance": float(index) + 0.25,
        "notes": note,
        "is_active": index % 2 == 0,
    }


def make_user_payloads(size: int) -> List[Dict[str, object]]:
    return [make_user_payload(index) for index in range(size)]


def payload_count_for_size(size: str) -> int:
    return {
        "small": 100,
        "medium": 1000,
        "large": 10000,
    }.get(size, 100)
