"""Small, testable parsers for Cambridge Dictionary's server-rendered HTML."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

BASE_URL = "https://dictionary.cambridge.org"
_SPACE_RE = re.compile(r"\s+")
_VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source",
    "track", "wbr",
}


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[tuple[str, str]] = []
        self._href: str | None = None
        self._depth = 0
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a" and self._href is None:
            self._href = dict(attrs).get("href")
            self._depth = 1
            self._text = []
        elif self._href is not None and tag not in _VOID_ELEMENTS:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._href is None:
            return
        self._depth -= 1
        if self._depth == 0:
            text = _SPACE_RE.sub(" ", "".join(self._text)).strip()
            self.anchors.append((self._href, text))
            self._href = None
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)


def _anchors(html: str) -> list[tuple[str, str]]:
    parser = _AnchorParser()
    parser.feed(html)
    return parser.anchors


def parse_range_urls(html: str, letter: str) -> list[str]:
    """Return range-page URLs from one `/browse/english/<letter>/` page."""
    root_path = f"/browse/english/{letter}/"
    urls = {
        urljoin(BASE_URL, href)
        for href, _ in _anchors(html)
        if urlsplit(urljoin(BASE_URL, href)).path.startswith(root_path)
        and urlsplit(urljoin(BASE_URL, href)).path != root_path
    }
    return sorted(urls)


def parse_words(html: str, length: int) -> dict[str, str]:
    """Return lowercase ASCII headwords and their canonical entry URLs."""
    result: dict[str, str] = {}
    expected = re.compile(rf"[a-z]{{{length}}}")
    for href, text in _anchors(html):
        absolute = urljoin(BASE_URL, href)
        if not urlsplit(absolute).path.startswith("/dictionary/english/"):
            continue
        if expected.fullmatch(text):
            result.setdefault(text, absolute)
    return result


class _DefinitionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.definition: str | None = None
        self._depth = 0
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        classes = set(attributes.get("class", "").split())
        if self.definition is None and self._depth == 0 and "ddef_d" in classes:
            self._depth = 1
            self._text = []
        elif self._depth and tag not in _VOID_ELEMENTS:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._depth:
            return
        self._depth -= 1
        if self._depth == 0:
            value = _SPACE_RE.sub(" ", "".join(self._text)).strip()
            self.definition = value.removesuffix(":").strip() or None

    def handle_data(self, data: str) -> None:
        if self._depth:
            self._text.append(data)


def parse_meaning(html: str) -> str | None:
    """Return the first English definition from an entry page."""
    parser = _DefinitionParser()
    parser.feed(html)
    return parser.definition
