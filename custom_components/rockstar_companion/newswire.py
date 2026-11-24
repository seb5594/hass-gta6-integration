"""Read an optional user-configured RSS, Atom or JSON feed."""

from __future__ import annotations

import asyncio
import json
import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .models import NewswireItem

_LOGGER = logging.getLogger(__name__)
_MAX_BYTES = 1024 * 1024
_ATOM = "{http://www.w3.org/2005/Atom}"


def is_feed_url(url: str) -> bool:
    """Accept HTTP(S) URLs with a host."""
    try:
        parts = urlsplit(url)
        return parts.scheme in {"http", "https"} and bool(parts.hostname)
    except ValueError:
        return False


async def async_fetch_newswire(hass: HomeAssistant, url: str) -> NewswireItem | None:
    """Return the first valid post from a bounded feed response."""
    try:
        async with (
            asyncio.timeout(10),
            async_get_clientsession(hass).get(url) as response,
        ):
            response.raise_for_status()
            body = bytearray()
            async for chunk in response.content.iter_chunked(16384):
                body.extend(chunk)
                if len(body) > _MAX_BYTES:
                    return None
        return parse_newswire(bytes(body))
    except (ClientError, TimeoutError, ValueError, ET.ParseError):
        _LOGGER.debug("Could not refresh the configured Newswire feed")
        return None


def parse_newswire(body: bytes) -> NewswireItem | None:
    """Parse the latest available headline without fetching external resources."""
    body = body.removeprefix(b"\xef\xbb\xbf")
    if body.lstrip().startswith((b"{", b"[")):
        data = json.loads(body)
        items = data.get("items", []) if isinstance(data, dict) else data
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("title"), str):
                    headline = item["title"].strip()
                    if headline:
                        return NewswireItem(
                            headline[:240],
                            str(item.get("url") or item.get("link") or ""),
                            str(
                                item.get("date_published")
                                or item.get("published")
                                or item.get("date")
                                or ""
                            ),
                        )
        return None

    # Ordinary feeds do not need DTDs or custom entities.
    upper_body = body.upper().replace(b"\x00", b"")
    if b"<!DOCTYPE" in upper_body or b"<!ENTITY" in upper_body:
        return None
    root = ET.fromstring(body)
    for item in root.iter("item"):
        if title := (item.findtext("title") or "").strip():
            return NewswireItem(
                title[:240], item.findtext("link") or "", item.findtext("pubDate") or ""
            )
    for item in root.iter(f"{_ATOM}entry"):
        if title := "".join(item.findtext(f"{_ATOM}title") or "").strip():
            for link in item.findall(f"{_ATOM}link"):
                if link.get("rel", "alternate") == "alternate":
                    return NewswireItem(
                        title[:240],
                        link.get("href", ""),
                        item.findtext(f"{_ATOM}updated") or "",
                    )
            return NewswireItem(
                title[:240], published=item.findtext(f"{_ATOM}updated") or ""
            )
    return None
