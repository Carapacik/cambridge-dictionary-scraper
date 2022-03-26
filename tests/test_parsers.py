import unittest

from cambridge_dictionary_scraper.parsers import parse_meaning, parse_range_urls, parse_words


class ParserTests(unittest.TestCase):
    def test_range_urls_from_current_browse_shape(self):
        html = '''
        <a href="https://dictionary.cambridge.org/browse/english/a/">a</a>
        <a class="hdb" href="https://dictionary.cambridge.org/browse/english/a/aardvark/">
          <span>aardvark</span> ... abdicate
        </a>
        <a href="/browse/english/a/abdicate-responsibility/">abdicate ... ability</a>
        <a href="/browse/english/b/baby/">not a range for a</a>
        '''
        self.assertEqual(
            parse_range_urls(html, "a"),
            [
                "https://dictionary.cambridge.org/browse/english/a/aardvark/",
                "https://dictionary.cambridge.org/browse/english/a/abdicate-responsibility/",
            ],
        )

    def test_words_are_lowercase_ascii_and_exact_length(self):
        html = '''
        <ul><li><a href="/dictionary/english/aback"><span>aback</span></a></li>
        <li><a href="/dictionary/english/aave">AAVE</a></li>
        <li><a href="/dictionary/english/ab-initio">ab initio</a></li>
        <li><a href="/dictionary/english/abase">abase</a></li></ul>
        '''
        self.assertEqual(
            parse_words(html, 5),
            {
                "aback": "https://dictionary.cambridge.org/dictionary/english/aback",
                "abase": "https://dictionary.cambridge.org/dictionary/english/abase",
            },
        )

    def test_first_definition_is_flattened_and_trailing_colon_removed(self):
        html = '''
        <div class="sense-body dsense_b"><div class="ddef_h">
          <div class="def ddef_d db">a round <a href="/dictionary/english/fruit">fruit</a>:</div>
        </div></div>
        <div class="def ddef_d db">second definition</div>
        '''
        self.assertEqual(parse_meaning(html), "a round fruit")

    def test_missing_definition(self):
        self.assertIsNone(parse_meaning("<html><body>blocked</body></html>"))


if __name__ == "__main__":
    unittest.main()

