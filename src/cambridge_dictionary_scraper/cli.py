"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .client import HttpClient
from .parsers import BASE_URL, parse_meaning, parse_range_urls
from .scraper import Scraper, validate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cambridge-scraper")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    commands = parser.add_subparsers(dest="command", required=True)

    def scraping_command(name: str, help_text: str) -> argparse.ArgumentParser:
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--word-length", "--length", dest="word_length", type=int, default=5)
        command.add_argument("--output-dir", "--output", dest="output_dir", type=Path)
        command.add_argument(
            "--delay", type=float, default=0.5, help="minimum seconds between requests"
        )
        command.add_argument("--retries", type=int, default=4)
        command.add_argument("--timeout", type=float, default=30.0)
        return command

    scraping_command("words", "collect words only")
    scraping_command("meanings", "collect meanings for existing words")
    scraping_command("all", "collect words and meanings")
    check = commands.add_parser("validate", help="validate output artifacts")
    check.add_argument("--word-length", "--length", dest="word_length", type=int, default=5)
    check.add_argument("--output-dir", "--output", dest="output_dir", type=Path)
    smoke = scraping_command("smoke", "check current Cambridge HTML without writing results")
    return parser


def main(arguments: list[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    output = args.output_dir or Path(f"results/{args.word_length}-letter")
    if args.command == "validate":
        errors = validate(output, args.word_length)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print(f"OK: {output}")
        return 0

    client = HttpClient(delay=args.delay, retries=args.retries, timeout=args.timeout)
    if args.command == "smoke":
        browse_url = f"{BASE_URL}/browse/english/a/"
        ranges = parse_range_urls(client.get(browse_url), "a")
        definition = parse_meaning(
            client.get(f"{BASE_URL}/dictionary/english/apple", referer=browse_url)
        )
        if not ranges or not definition:
            print("ERROR: expected server-rendered links/definition were not found")
            return 1
        print(f"OK: {len(ranges)} range links; apple: {definition}")
        return 0

    scraper = Scraper(client, output, args.word_length)
    if args.command == "words":
        scraper.collect_words()
    elif args.command == "meanings":
        scraper.collect_meanings()
    else:
        scraper.run()
    return 0
