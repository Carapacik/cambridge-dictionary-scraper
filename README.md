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
- failsFileName - File for failed links
- wordsFileName - File for all words we get
- wordsFileFormat - File format for outputs