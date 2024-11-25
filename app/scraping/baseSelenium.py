from selenium.webdriver import Chrome
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import time

def main():

    #configuracion para abrir la web.
    service = Service(ChromeDriverManager().install())
    option = webdriver.ChromeOptions()

    #corre la web como "minimizada."
    #option.add_argument("--headless")

    option.add_argument("--window-size=1920,1080")
    driver = Chrome(service=service, options=option)

    driver.get("#") #link completo de la web.
    time.sleep(5)
    driver.quit()

if __name__=="__main__":
    main()