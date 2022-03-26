# cambridge-dictionary-scraper

A small Python package that scrapes English words and their meanings from
[Cambridge Dictionary](https://dictionary.cambridge.org/).

The generated dictionary is used by the
[Wordly Plus game on Google Play](https://play.google.com/store/apps/details?id=com.carapacik.wordly).
The game source is in the [wordly-plus repository](https://github.com/Carapacik/wordly-plus).

## Requirements

- Python 3.14 or newer

```console
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Chrome and ChromeDriver are no longer required: Cambridge Dictionary returns
browse links, words, and meanings in its server-rendered HTML. The scraper uses
only Python's standard library, with a cookie session and browser-compatible
navigation headers.

## Usage

Collect all five-letter English words over HTTP into `results/5-letter/`:

```console
.venv\Scripts\cambridge-scraper words
```

Then collect their meanings:

```console
.venv\Scripts\cambridge-scraper meanings
```

Or run both stages:

```console
.venv\Scripts\cambridge-scraper all
```

Quick two-request smoke test:

```console
.venv\Scripts\cambridge-scraper smoke
```

The result directory contains:

- `words.txt` — sorted unique lowercase ASCII words;
- `meanings.json` — a UTF-8 JSON object keyed by word;
- `failures.json` — failed browse and meaning requests with their errors;
- `word-urls.json` — the canonical Cambridge URL for every word;
- `checkpoint.json` — completed letters and browse ranges.

Requests are single-threaded and have a default minimum delay of 0.5 seconds.
Temporary HTTP errors use bounded exponential backoff. Progress is written
atomically after every browse range and every ten meanings. Repeating a command
resumes from these files instead of starting over.

For another word length, `words --word-length 6` automatically uses
`results/6-letter/`. You can override the result location with `--output-dir`.

Validate an existing result:

```console
.venv\Scripts\cambridge-scraper validate
```

Use `cambridge-scraper --help`, `cambridge-scraper words --help`, or
`cambridge-scraper meanings --help` for all options.

Please keep a conservative request delay and review the website's current terms
before collecting or redistributing data. This project is not affiliated with
Cambridge University Press & Assessment.

## Tests

```console
.venv\Scripts\python -m unittest discover -s tests
```
