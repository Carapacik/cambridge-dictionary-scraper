# Scraper for Cambridge Dictionary

Get words from dictionary.cambridge.org

Used this to get dictionary for [Wordle App](https://github.com/Carapacik/Wordle)

## Install
Python 3.5 or higher is required
```
$ pip install selenium
$ pip install selenium-stealth
```
Download latest stable release ChromeDriver from here 
https://chromedriver.chromium.org/

## Usage
- baseUrl - Url where we will get the data from
- chromeDriverPath - Path to your chromedriver
- lettersNumber - How long are we searching for words
- programFileFormat - File format for outputs
- failsFileName - File for failed links
- wordsFileName - File for all words we get
- meaningFileName - File for all words with meanings we get 

Run get_all_words.py to get all words from dictionary
Run get_words_meaning.py to get all words meaning (You must have a completed file with the words: word.txt)