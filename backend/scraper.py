from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json
import time
from datetime import datetime
import urllib.parse
import logging
import os
import glob
import random
from selenium.webdriver.chrome.options import Options

# Import virtual display for headless servers
try:
    from pyvirtualdisplay import Display
    VIRTUAL_DISPLAY_AVAILABLE = True
except ImportError:
    VIRTUAL_DISPLAY_AVAILABLE = False
    logging.warning("pyvirtualdisplay not available. Virtual display will not be used.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInJobScraper:
    def __init__(self):
        self.driver = None
        self.jobs_per_page = 25
        self.virtual_display = None

    def setup_driver(self):
        try:
            # Setup virtual display for headless servers
            if VIRTUAL_DISPLAY_AVAILABLE:
                try:
                    logger.info("Setting up virtual display...")
                    self.virtual_display = Display(visible=0, size=(1920, 1080))
                    self.virtual_display.start()
                    logger.info("Virtual display started successfully")
                except Exception as e:
                    logger.warning(f"Failed to setup virtual display: {e}")
                    self.virtual_display = None
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')
            options.add_argument('--blink-settings=imagesEnabled=false')
            options.add_argument('--remote-debugging-port=9222')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            
            # Try multiple Chrome/Chromium binaries with better detection
            chrome_binaries = [
                '/usr/bin/google-chrome-stable',
                '/usr/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/snap/bin/chromium',
                '/usr/bin/chrome',
                '/usr/bin/chromium-browser-stable',
            ]
            
            chrome_found = False
            for binary in chrome_binaries:
                if os.path.exists(binary):
                    options.binary_location = binary
                    chrome_found = True
                    logger.info(f"Found Chrome/Chromium at: {binary}")
                    break
            
            if not chrome_found:
                logger.warning("No Chrome/Chromium binary found in standard locations")
                # Try to find it using which command
                try:
                    import subprocess
                    result = subprocess.run(['which', 'chromium-browser'], capture_output=True, text=True)
                    if result.returncode == 0:
                        binary_path = result.stdout.strip()
                        options.binary_location = binary_path
                        chrome_found = True
                        logger.info(f"Found Chrome/Chromium using 'which': {binary_path}")
                except Exception as e:
                    logger.warning(f"Could not find Chrome/Chromium using 'which': {e}")
            
            if not chrome_found:
                logger.warning("No Chrome/Chromium binary found, trying default")
            
            # Use webdriver-manager by default for better reliability
            try:
                logger.info("Using webdriver-manager to setup Chrome WebDriver...")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("Chrome WebDriver setup successful with webdriver-manager")
            except Exception as wdm_error:
                logger.warning(f"WebDriver-manager failed: {wdm_error}")
                
                # Fallback: Try without service
                try:
                    logger.info("Trying fallback without service...")
                    self.driver = webdriver.Chrome(options=options)
                    logger.info("Chrome WebDriver setup successful without service")
                except Exception as final_error:
                    logger.error(f"All Chrome setup attempts failed: {final_error}")
                    raise Exception(f"Could not setup Chrome WebDriver. Please install Chrome/Chromium: sudo apt install -y chromium-browser")
                        
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {str(e)}")
            raise

    def construct_linkedin_url(self, search_query, location=None, start=0):
        base_url = "https://www.linkedin.com/jobs/search?"
        params = {
            "keywords": search_query,
            "location": location if location else "",
            "position": 1,
            "pageNum": start // self.jobs_per_page,
            "start": start,
            "sortBy": "DD"  # Most recent
        }
        url = base_url + urllib.parse.urlencode({k: v for k, v in params.items() if v})
        logger.info(f"Constructed URL: {url}")
        return url

    def wait_and_get_element(self, by, value, timeout=60, multiple=False):
        try:
            if multiple:
                elements = self.driver.find_elements(by, value)
                return elements
            else:
                element = self.driver.find_element(by, value)
                return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {value}")
            self.driver.quit()
            return [] if multiple else None

    def scroll_to_element(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(random.uniform(1, 2))  # Random delay to appear more human-like

    def get_job_cards(self, retries=3):
        while retries > 0:
            try:
                # Try different selectors for job cards
                selectors = [
                    "div.job-card-container",
                    "li.jobs-search-results__list-item",
                    "div.base-card",
                    "div.job-search-card"
                ]
                
                for selector in selectors:
                    job_cards = self.wait_and_get_element(
                        By.CSS_SELECTOR, 
                        selector,
                        multiple=True
                    )
                    if job_cards:
                        logger.info(f"Found job cards using selector: {selector}")

                        return job_cards
                
                retries -= 1
                time.sleep(random.uniform(2, 3))
            except Exception as e:
                logger.error(f"Error finding job cards: {e}")
                retries -= 1
        return []

    def scrape_jobs(self, search_query, location=None, num_jobs=8):
        try:
            if not self.driver:
                self.setup_driver()

            jobs = []
            start = 0
            pages_without_new_jobs = 0
            max_pages_without_new_jobs = 2
            max_retries_per_page = 2
            
            # Add timeout mechanism
            start_time = time.time()
            timeout = 60  # 90 seconds timeout

            while len(jobs) < num_jobs and pages_without_new_jobs < max_pages_without_new_jobs:
                # Check if timeout reached
                if time.time() - start_time > timeout:
                    logger.info("Timeout reached (60 seconds). Stopping scraping.")
                    break

                url = self.construct_linkedin_url(search_query, location, start)
                self.driver.get(url)
                time.sleep(random.uniform(2, 3))

                # Get initial job cards
                job_cards = self.get_job_cards(retries=max_retries_per_page)
                
                if not job_cards:
                    logger.warning(f"No job cards found on page {start // self.jobs_per_page + 1}")
                    pages_without_new_jobs += 1
                    start += self.jobs_per_page
                    continue

                initial_jobs_count = len(jobs)
                logger.info(f"Found {len(job_cards)} job cards on page {start // self.jobs_per_page + 1}")

                # Process only enough cards to reach num_jobs
                cards_to_process = min(len(job_cards), num_jobs - len(jobs))
                logger.info(f"Processing {cards_to_process} cards to reach target of {num_jobs} jobs")

                for i in range(cards_to_process):
                    # Check timeout again for each card
                    if time.time() - start_time > timeout:
                        logger.info("Timeout reached (60 seconds). Stopping scraping.")
                        break

                    try:
                        card = job_cards[i]
                        self.scroll_to_element(card)
                        time.sleep(random.uniform(0.5, 1))
                        
                        # Extract job details with better error handling
                        title = company = location_text = "Not available"
                        job_link = None
                        
                        try:
                            title_elem = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title, h3.job-card-list__title")
                            title = title_elem.text.strip()
                        except Exception as e:
                            logger.warning(f"Could not extract title: {e}")
                            continue

                        try:
                            company_elem = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle, h4.job-card-container__company-name")
                            company = company_elem.text.strip()
                        except Exception as e:
                            logger.warning(f"Could not extract company: {e}")

                        try:
                            location_elem = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location, div.job-card-container__metadata-item")
                            location_text = location_elem.text.strip()
                        except Exception as e:
                            logger.warning(f"Could not extract location: {e}")

                        # Get job link without clicking
                        try:
                            link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link, a.job-card-list__title-link")
                            job_link = link_elem.get_attribute('href')
                        except Exception:
                            try:
                                # Fallback: try to find any link in the card
                                link_elem = card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                                job_link = link_elem.get_attribute('href')
                            except Exception as e:
                                logger.warning(f"Could not extract job URL: {e}")
                                continue

                        if not job_link:
                            continue

                        # Create job object without description (since we're not clicking)
                        job = {
                            "id": str(len(jobs) + 1),
                            "title": title,
                            "company": company,
                            "location": location_text,
                            "description": "Click the link to view full job description on LinkedIn",
                            "postedDate": datetime.now().strftime("%Y-%m-%d"),
                            "url": job_link
                        }
                        
                        logger.info(f"Scraped job {len(jobs) + 1}/{num_jobs}: {job['title']} at {job['company']}")
                        jobs.append(job)

                        if len(jobs) >= num_jobs:
                            logger.info(f"Reached target of {num_jobs} jobs")
                            break

                    except Exception as e:
                        logger.error(f"Error processing job card {i + 1}: {str(e)}")
                        continue

                if len(jobs) == initial_jobs_count:
                    pages_without_new_jobs += 1
                else:
                    pages_without_new_jobs = 0

                if len(jobs) >= num_jobs:
                    break

                start += self.jobs_per_page
                time.sleep(random.uniform(1.5, 2))

            logger.info(f"Completed scraping with {len(jobs)} jobs found")
            return jobs

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.error(f"Error closing WebDriver: {str(e)}")
            
            # Clean up virtual display
            if self.virtual_display:
                try:
                    self.virtual_display.stop()
                    logger.info("Virtual display stopped")
                except Exception as e:
                    logger.error(f"Error stopping virtual display: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")
        
        if self.virtual_display:
            try:
                self.virtual_display.stop()
                logger.info("Virtual display stopped")
            except Exception as e:
                logger.error(f"Error stopping virtual display: {str(e)}")

    def save_to_file(self, jobs, filename="jobs.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({"jobs": jobs}, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    scraper = LinkedInJobScraper()
    jobs = scraper.scrape_jobs("python developer", "Remote")
    scraper.save_to_file(jobs)
    print(f"Scraped {len(jobs)} jobs successfully!") 