import time
import re
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from typing import Final

lettersNumber: Final = 5
baseUrl: Final = "https://dictionary.cambridge.org/browse/english"
chromeDriverPath: Final = r"C:/Users/User/Documents/chromedriver.exe"
wordsFileName: Final = "words.txt"

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


file = open(wordsFileName, "w")
letters = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]
for letter in letters:
    url = f"{baseUrl}/{letter}/"
    driver.get(url)
    block1 = driver.find_element(
        By.CSS_SELECTOR,
        "body > div.cc.fon > div > div > div.hfr-m.ltab.lp-m_l-15 > div.x.lmt-15 > div.hfl-s.lt2b.lmt-10.lmb-25.lp-s_r-20 > div.hdf.ff-50.lmt-15 > div.lc.lpr-2 > ul",
    )
    data1 = findWords(block1)
    block2 = driver.find_element(
        By.CSS_SELECTOR,
        "body > div.cc.fon > div > div > div.hfr-m.ltab.lp-m_l-15 > div.x.lmt-15 > div.hfl-s.lt2b.lmt-10.lmb-25.lp-s_r-20 > div.hdf.ff-50.lmt-15 > div.lpl-2 > ul",
    )
    data2 = findWords(block2)

    data1 += data2
    time.sleep(1)

    for wordBegin in data1:
        correctWord = (
            wordBegin.replace(" & ", "-")
            .replace(", ", "-")
            .replace(". ", "-")
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
            if re.fullmatch(rf"[A-Za-z]{lettersNumber}", word):
                if not re.fullmatch(r"[A-Z]", word):
                    file.write(word + "\n")
    print(f"Complete for letter {letter}")

print("All complete")
file.close()
time.sleep(1)
driver.quit()