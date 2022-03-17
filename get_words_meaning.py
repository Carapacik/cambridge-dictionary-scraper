from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from typing import Final

baseUrl: Final = r"https://dictionary.cambridge.org/dictionary/english"
chromeDriverPath: Final = r"C:/Users/User/Documents/chromedriver.exe"
wordsFileName: Final = "word"
failsFileName: Final = "meaning_fails"
meaningFileName: Final = "meaning"
programFileFormat: Final = "txt"

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


def getMeaningBloc(driver):
    block = driver.find_element(By.CLASS_NAME, "sense-body")
    return block.find_element(By.CLASS_NAME, "ddef_d")


fileWithFails = open(f"{failsFileName}.{programFileFormat}", "w")
fileWithMeaningWords = open(f"{meaningFileName}.{programFileFormat}", "w")
with open(f"{wordsFileName}.{programFileFormat}", "r") as fileWithWords:
    for word in fileWithWords:
        url = f"{baseUrl}/{word.lower()}"
        driver.get(url)
        try:
            blockDescription = getMeaningBloc(driver)
            blockDescriptionText: str = blockDescription.text
            # meaning of the word on another page is the link
            if (
                blockDescriptionText.startswith("plural of")
                or blockDescriptionText.startswith("past simple")
                or blockDescriptionText.startswith("present participle")
                or blockDescriptionText.startswith("→")
                or "US spelling of" in blockDescriptionText
                or "UK spelling of" in blockDescriptionText
                or "another spelling of" in blockDescriptionText
            ):
                singularMeaningUrl = blockDescription.find_element(
                    By.TAG_NAME, "a"
                ).get_attribute("href")
                driver.get(singularMeaningUrl)
                blockDescription = getMeaningBloc(driver)
                blockDescriptionText = blockDescription.text
            fixedMeaning: str = blockDescriptionText
            # if ':' in the end of string
            if blockDescriptionText[-1] == ":":
                fixedMeaning = blockDescriptionText[:-1]
            # capitalize only first letter
            fixedMeaning = fixedMeaning[0].upper() + fixedMeaning[1:]
            # replace " to \" for code files
            fixedMeaning = fixedMeaning.replace('"', '\\"')
            fileWithMeaningWords.write(
                f'"{word[:-1].lower()}": "{fixedMeaning}",\n')
        except:
            # meaning of the word is not on the page
            fileWithFails.write(url)

fileWithWords.close()
fileWithFails.close()
fileWithMeaningWords.close()
driver.quit()
