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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInJobScraper:
    def __init__(self):
        self.driver = None
        self.jobs_per_page = 25

    def setup_driver(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-notifications')
            options.add_argument('--lang=en-US')
            
            # Add more realistic user agent
            options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
            
            # Additional options to avoid detection
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Install ChromeDriver
            driver_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(driver_path)
            
            # Find the actual chromedriver executable
            chromedriver_path = None
            for root, dirs, files in os.walk(driver_dir):
                for file in files:
                    if file == 'chromedriver':
                        chromedriver_path = os.path.join(root, file)
                        break
            
            if not chromedriver_path:
                raise Exception("Could not find chromedriver executable")
            
            # Make sure it's executable
            os.chmod(chromedriver_path, 0o755)
            logger.info(f"ChromeDriver path: {chromedriver_path}")
            
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.implicitly_wait(10)
            logger.info("WebDriver setup complete")
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
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

    def wait_and_get_element(self, by, value, timeout=20, multiple=False):
        try:
            if multiple:
                elements = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located((by, value))
                )
                return elements
            else:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {value}")
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
            timeout = 60  # 60 seconds timeout

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

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return jobs

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.error(f"Error closing WebDriver: {str(e)}")

    def save_to_file(self, jobs, filename="jobs.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({"jobs": jobs}, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    scraper = LinkedInJobScraper()
    jobs = scraper.scrape_jobs("python developer", "Remote")
    scraper.save_to_file(jobs)
    print(f"Scraped {len(jobs)} jobs successfully!") 