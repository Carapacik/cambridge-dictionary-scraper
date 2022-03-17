import time
import re
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from typing import Final

baseUrl: Final = r"https://dictionary.cambridge.org/browse/english"
chromeDriverPath: Final = r"C:/Users/User/Documents/chromedriver.exe"
lettersNumber: Final = 5
failsFileName: Final = "word_fails"
wordsFileName: Final = "word"
programFileFormat: Final = "txt"
letters: Final = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                  "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("--ignore-certificate-errors-spki-list")
driver = webdriver.Chrome(options=options, executable_path=chromeDriverPath)
stealth(
    driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
    run_on_insecure_origins=False,
)


def findWords(block):
    wordBlocks = block.find_elements(By.TAG_NAME, "li")
    data = []
    for element in wordBlocks:
        finalWord = element.find_element(
            By.CSS_SELECTOR, "a > span:nth-child(1) > span > span"
        ).text
        data.append(finalWord)
    return data


def findWordsInBegin(wordBeginBlock):
    wordBlocks = wordBeginBlock.find_elements(By.TAG_NAME, "li")
    data = []
    for element in wordBlocks:
        finalWord = element.find_element(
            By.CSS_SELECTOR, "a > span > span > span > span"
        ).text
        if len(finalWord) == lettersNumber:
            data.append(finalWord)
    return data


fileWithFails = open(f"{failsFileName}.{programFileFormat}", "w")
fileWithWords = open(f"{wordsFileName}.{programFileFormat}", "w")
for letter in letters:
    url = f"{baseUrl}/{letter}/"
    driver.get(url)
    try:
        block1 = driver.find_element(
            By.CSS_SELECTOR,
            "body > div.cc.fon > div > div > div.hfr-m.ltab.lp-m_l-15 > div.x.lmt-15 > div.hfl-s.lt2b.lmt-10.lmb-25.lp-s_r-20 > div.hdf.ff-50.lmt-15 > div.lc.lpr-2 > ul",
        )
        data1 = findWords(block1)
        try:
            # if there is no second column
            block2 = driver.find_element(
                By.CSS_SELECTOR,
                "body > div.cc.fon > div > div > div.hfr-m.ltab.lp-m_l-15 > div.x.lmt-15 > div.hfl-s.lt2b.lmt-10.lmb-25.lp-s_r-20 > div.hdf.ff-50.lmt-15 > div.lpl-2 > ul",
            )
            data2 = findWords(block2)
        except:
            data2 = []
        data1 += data2
    except:
        fileWithFails.write(url + "\n\n")
    time.sleep(1)
    for wordBegin in data1:
        # if starts with -> '
        wordStartWithApostrophe: str = wordBegin
        if wordBegin[0] == "'":
            wordStartWithApostrophe = wordBegin[1:]
        # if starts with -> the
        wordStartWithThe: str = wordStartWithApostrophe
        if wordStartWithApostrophe[:4].lower() == "the ":
            wordStartWithThe = wordStartWithApostrophe[4:]
        # for correct adress inn browser bar
        correctWord: str = (
            wordStartWithThe
            .replace("é", "e")
            .replace("è", "e")
            .replace("ä", "a")
            .replace(" & ", "-")
            .replace(" ... ", "-")
            .replace(", ", "-")
            .replace(". ", "-")
            .replace(" '", "-")
            .replace("/", "-")
            .replace("'", "-")
            .replace(",", "-")
            .replace(".", "")
            .replace("/", "")
            .replace("(", "")
            .replace(")", "")
            .replace("?", "")
            .replace("!", "")
            .replace(" ", "-")
            .lower()
        )
        wordBeginUrl = f"{baseUrl}/{letter}/{correctWord}"
        driver.get(wordBeginUrl)
        try:
            wordBeginBlock1 = driver.find_element(
                By.CSS_SELECTOR,
                "body > div.cc.fon > div > div > div.hfr-m.ltab.lp-m_l-15 > div.x.lmt-15 > div.hfl-s.lt2b.lmt-10.lmb-25.lp-s_r-20 > div.hdf.ff-50.lmt-15 > div.lc.lc6-12.lpr-2 > ul",
            )
            wordBeginData1 = findWordsInBegin(wordBeginBlock1)
            wordBeginBlock2 = driver.find_element(
                By.CSS_SELECTOR,
                "body > div.cc.fon > div > div > div.hfr-m.ltab.lp-m_l-15 > div.x.lmt-15 > div.hfl-s.lt2b.lmt-10.lmb-25.lp-s_r-20 > div.hdf.ff-50.lmt-15 > div.lpl-2 > ul",
            )
            wordBeginData2 = findWordsInBegin(wordBeginBlock2)
            wordBeginData1 += wordBeginData2
            for word in wordBeginData1:
                # filtering words with only english letters
                if re.fullmatch(r"[a-zA-Z]+", word):
                    # filtering abbreviations
                    if not re.fullmatch(r"[A-Z]+", word):
                        fileWithWords.write(word + "\n")
        except:
            fileWithFails.write(wordBeginUrl + "\n")
    print(f"Complete for letter {letter}")

fileWithWords.close()
fileWithFails.close()
time.sleep(1)
driver.quit()
