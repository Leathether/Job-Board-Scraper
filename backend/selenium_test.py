from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os

CHROMEDRIVER_PATH = os.path.expanduser(
    '~/.wdm/drivers/chromedriver/linux64/138.0.7204.94/chromedriver-linux64/chromedriver'
)

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

try:
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    driver.get('https://www.google.com')
    print('Title:', driver.title)
    driver.quit()
    print('Selenium test succeeded!')
except Exception as e:
    print('Selenium test failed:', e) 