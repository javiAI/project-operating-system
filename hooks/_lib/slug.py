"""Slug helpers shared across pos hooks."""
from __future__ import annotations


def sanitize_slug(slug: str) -> str:
    return slug.replace("/", "_")
