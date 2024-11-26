import os
import json
import time
import random
import logging
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define url
url = "https://stockanalysis.com/list/biggest-companies/"

# Define output path
data_dir = 'src/data/'
os.makedirs(os.path.dirname(data_dir), exist_ok=True)

# Define Chrome webdriver options
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--enable-javascript')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

# Try to initialize webdriver
try: 
    driver = webdriver.Chrome()
except Exception as e: 
    logging.error(f"Failed to initialize WebDriver: {str(e)}")
    raise
logging.info(f"WebDriver successfully initialized")

# Begin scraping tickers from website
try:
    current_page = 1
    all_tickers = []
    
    logging.info(f"Navigating to URL: {url}")
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    logging.info("Page loaded successfully")
    
    # Enter loop to scrape data from each page of site
    while True: 
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        ticker_elements = soup.find_all("td", class_="sym svelte-eurwtr")
        logging.info(f"Number of tickers found on page {current_page}: {len(ticker_elements)}")
        
        if not ticker_elements: 
            logging.warning("No tickers found. The HTML structure might have changed.")
            exit(1)
            
        tickers = [ticker_element.a.text.strip() for ticker_element in ticker_elements]
        all_tickers.extend(tickers)
        
        # Save tickers to a JSON file
        tickers_data = {"tickers": all_tickers}
        with open(os.path.join(data_dir, 'tickers.json'), 'w') as f: 
            json.dump(tickers_data, f)
        logging.info(f"Tickers on page {current_page} saved to tickers.json")
        
        # Move to next page and increment page count
        next_button_xpath = "//button[contains(@class, 'controls-btn') and contains(@class, 'xs:pl-1') and contains(@class, 'xs:pr-1.5') and contains(@class, 'bp:text-sm') and contains(@class, 'sm:pl-3') and contains(@class, 'sm:pr-1')]/span[text()='Next']"
        try:
            next_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, next_button_xpath))
            )
            
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            
            next_button = driver.find_element(By.XPATH, next_button_xpath)
            
            if 'disabled' in next_button.get_attribute("class"): 
                logging.info("Next button is disabled. Exiting pagination")
                break
            
            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, next_button_xpath))
            )

            try:
                next_button.click()
                logging.info("Navigated to next page successfully")
            except ElementClickInterceptedException:
                logging.warning("Element click intercepted. Retrying...")
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                try:
                    next_button.click()
                    logging.info("Navigated to next page successfully after retry")
                except ElementClickInterceptedException:
                    logging.error("Element click intercepted again. Exiting pagination.")
                    break

            current_page += 1
            wait_time = random.uniform(1, 2)
            time.sleep(wait_time)
            
        except TimeoutException:
            logging.error("Timeout occurred: Next button not found or not clickable.")
            break
        
        except NoSuchElementException:
            logging.error("Next button not found.")
            break   
        
        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            break
    
    logging.info(f"Total number of tickers gathered: {len(all_tickers)}")
    
except Exception as e: 
    logging.error(f"An error occurred during scraping: {str(e)}")
    raise

finally: 
    driver.quit()
    logging.info("Scraping finished. Webdriver closed")
