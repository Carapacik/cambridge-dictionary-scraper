"""Resumable word-list and meaning collection."""

from __future__ import annotations

import string
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .client import FetchError, HttpClient
from .parsers import BASE_URL, parse_meaning, parse_range_urls, parse_words
from .storage import read_json, write_json, write_lines

Reporter = Callable[[str], None]


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def words(self) -> Path:
        return self.root / "words.txt"

    @property
    def word_urls(self) -> Path:
        return self.root / "word-urls.json"

    @property
    def meanings(self) -> Path:
        return self.root / "meanings.json"

    @property
    def failures(self) -> Path:
        return self.root / "failures.json"

    @property
    def checkpoint(self) -> Path:
        return self.root / "checkpoint.json"


class Scraper:
    def __init__(
        self, client: HttpClient, output: Path, length: int, report: Reporter = print
    ) -> None:
        if length < 1:
            raise ValueError("length must be positive")
        self.client = client
        self.paths = Paths(output)
        self.length = length
        self.report = report
        self.paths.root.mkdir(parents=True, exist_ok=True)

    def _checkpoint(self) -> dict:
        checkpoint = read_json(
            self.paths.checkpoint,
            {
                "version": 1,
                "word_length": self.length,
                "completed_letters": [],
                "completed_ranges": [],
            },
        )
        if checkpoint.get("word_length") != self.length:
            raise ValueError("checkpoint belongs to a different word length")
        return checkpoint

    def collect_words(self) -> dict[str, str]:
        checkpoint = self._checkpoint()
        completed_letters = set(checkpoint["completed_letters"])
        completed_ranges = set(checkpoint["completed_ranges"])
        word_urls: dict[str, str] = read_json(self.paths.word_urls, {})
        failures: dict = read_json(self.paths.failures, {"browse": {}, "meanings": {}})

        for letter in string.ascii_lowercase:
            if letter in completed_letters:
                continue
            index_url = f"{BASE_URL}/browse/english/{letter}/"
            try:
                html = self.client.get(index_url)
                ranges = parse_range_urls(html, letter)
                if not ranges:
                    raise ValueError("no range links found")
            except (FetchError, ValueError) as error:
                failures["browse"][index_url] = str(error)
                write_json(self.paths.failures, failures)
                self.report(f"browse index failed: {letter}: {error}")
                continue

            for position, range_url in enumerate(ranges, 1):
                if range_url in completed_ranges:
                    continue
                try:
                    page = self.client.get(range_url, referer=index_url)
                    word_urls.update(parse_words(page, self.length))
                    completed_ranges.add(range_url)
                    failures["browse"].pop(range_url, None)
                except FetchError as error:
                    failures["browse"][range_url] = str(error)
                    self.report(f"browse range failed: {range_url}: {error}")
                checkpoint["completed_ranges"] = sorted(completed_ranges)
                if position % 10 == 0:
                    self.report(
                        f"words {letter}: {position}/{len(ranges)} ranges, {len(word_urls)} words"
                    )
                write_json(self.paths.word_urls, word_urls)
                write_lines(self.paths.words, sorted(word_urls))
                write_json(self.paths.failures, failures)
                write_json(self.paths.checkpoint, checkpoint)

            if all(url in completed_ranges for url in ranges):
                completed_letters.add(letter)
                failures["browse"].pop(index_url, None)
            checkpoint["completed_letters"] = sorted(completed_letters)
            write_json(self.paths.checkpoint, checkpoint)
            write_json(self.paths.failures, failures)
            self.report(f"words {letter}: complete, {len(word_urls)} total")
        return dict(sorted(word_urls.items()))

    def collect_meanings(self) -> dict[str, str]:
        word_urls: dict[str, str] = read_json(self.paths.word_urls, {})
        if not word_urls:
            raise RuntimeError("no words found; run the words stage first")
        meanings: dict[str, str] = read_json(self.paths.meanings, {})
        failures: dict = read_json(self.paths.failures, {"browse": {}, "meanings": {}})
        failures.setdefault("browse", {})
        failures.setdefault("meanings", {})

        pending = [(word, url) for word, url in sorted(word_urls.items()) if word not in meanings]
        for position, (word, url) in enumerate(pending, 1):
            try:
                html = self.client.get(url)
                meaning = parse_meaning(html)
                if not meaning:
                    raise ValueError("no definition found")
                meanings[word] = meaning
                failures["meanings"].pop(word, None)
            except (FetchError, ValueError) as error:
                failures["meanings"][word] = {"url": url, "error": str(error)}
            if position % 10 == 0 or position == len(pending):
                write_json(self.paths.meanings, meanings)
                write_json(self.paths.failures, failures)
            if position % 100 == 0:
                self.report(
                    f"meanings: {position}/{len(pending)} this run, "
                    f"{len(meanings)}/{len(word_urls)} total"
                )
        return dict(sorted(meanings.items()))

    def run(self) -> tuple[dict[str, str], dict[str, str]]:
        words = self.collect_words()
        meanings = self.collect_meanings()
        return words, meanings


def validate(output: Path, length: int) -> list[str]:
    paths = Paths(output)
    words = paths.words.read_text(encoding="utf-8").splitlines() if paths.words.exists() else []
    word_urls: dict[str, str] = read_json(paths.word_urls, {})
    meanings: dict[str, str] = read_json(paths.meanings, {})
    failures: dict = read_json(paths.failures, {"browse": {}, "meanings": {}})
    checkpoint: dict = read_json(paths.checkpoint, {})
    errors: list[str] = []
    if not words:
        errors.append("words.txt is missing or empty")
    if words != sorted(set(words)):
        errors.append("words.txt is not sorted and unique")
    invalid = [
        word
        for word in words
        if len(word) != length
        or not word.isascii()
        or not word.islower()
        or not word.isalpha()
    ]
    if invalid:
        errors.append(f"invalid words: {invalid[:10]}")
    if set(words) != set(word_urls):
        errors.append("words.txt and word-urls.json keys differ")
    if not set(meanings) <= set(words):
        errors.append("meanings.json contains unknown words")
    if any(not isinstance(value, str) or not value.strip() for value in meanings.values()):
        errors.append("meanings.json contains empty/non-string meanings")
    unresolved = set(words) - set(meanings) - set(failures.get("meanings", {}))
    if unresolved:
        errors.append(f"words have neither meaning nor failure: {sorted(unresolved)[:10]}")
    completed_letters = set(checkpoint.get("completed_letters", []))
    failed_letters = {
        url.split("/browse/english/", 1)[1].split("/", 1)[0]
        for url in failures.get("browse", {})
        if "/browse/english/" in url
    }
    unaccounted_letters = set(string.ascii_lowercase) - completed_letters - failed_letters
    if unaccounted_letters:
        errors.append(
            f"browse letters are neither complete nor failed: {sorted(unaccounted_letters)}"
        )
    return errors
