import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

class WebScraper:
    """
    A web scraper class for scraping judicial case information from a specific website.
    
    This class encapsulates the scraping logic with methods for setting up the webdriver,
    navigating through pages, and extracting case information.
    """

    def __init__(self, base_url: str = "http://scw.pjn.gov.ar/scw/home.seam"):
        """
        Initialize the web scraper with a base URL.
        
        Args:
            base_url (str): The base URL of the website to scrape.
        """
        self.base_url = base_url
        self.driver: Optional[WebDriver] = None
        self.logger = self._setup_logger()

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """
        Set up a logger for tracking scraping activities.
        
        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger('WebScraper')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def setup_driver(self) -> WebDriver:
        """
        Configure and return a Selenium WebDriver with options for container compatibility.
        
        Returns:
            WebDriver: Configured Chrome WebDriver.
        """
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver

    def wait_for_element(
        self, 
        by: By, 
        value: str, 
        timeout: int = 10
    ) -> Optional[WebElement]:
        """
        Wait for a specific element to be clickable.
        
        Args:
            by (By): Locator strategy (e.g., By.XPATH, By.ID)
            value (str): Locator value
            timeout (int): Maximum wait time in seconds
        
        Returns:
            Optional[WebElement]: The located element or None if not found
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except Exception as e:
            self.logger.error(f"Error waiting for element {by}={value}: {e}")
            return None

    def search_cases(self, search_term: str = "residuos"):
        """
        Perform initial case search with specified parameters.
        
        Args:
            search_term (str): Term to search in case details
        """
        # Navigate to base URL
        self.driver.get(self.base_url)

        # Click on 'porParte' tab
        self._click_part_tab()

        # Select jurisdiction
        self._select_jurisdiction()

        # Enter search term
        self._enter_search_term(search_term)

        # Prompt for CAPTCHA resolution
        input("Please resolve the CAPTCHA and press Enter to continue...")

        # Click search button
        self._click_search_button()

    def _click_part_tab(self):
        """Click on the 'porParte' tab."""
        tab = self.wait_for_element(By.XPATH, '//*[@id="formPublica:porParte:header:inactive"]')
        if tab:
            tab.click()
            self.logger.info("'porParte' tab clicked successfully.")
        else:
            self.logger.error("Could not click 'porParte' tab.")

    def _select_jurisdiction(self, jurisdiction_value: str = "10"):
        """
        Select jurisdiction from dropdown.
        
        Args:
            jurisdiction_value (str): Value of jurisdiction to select
        """
        jurisdiccion_select = self.wait_for_element(By.ID, "formPublica:camaraPartes")
        if jurisdiccion_select:
            select = Select(jurisdiccion_select)
            select.select_by_value(jurisdiction_value)
            self.logger.info("Jurisdiction option selected successfully.")
        else:
            self.logger.error("Could not find jurisdiction dropdown.")

    def _enter_search_term(self, search_term: str):
        """
        Enter search term into text input.
        
        Args:
            search_term (str): Term to search
        """
        input_element = self.wait_for_element(By.XPATH, '//*[@id="formPublica:nomIntervParte"]')
        if input_element:
            input_element.send_keys(search_term)
            self.logger.info(f"Search term '{search_term}' entered successfully.")
        else:
            self.logger.error("Could not find search input field.")

    def _click_search_button(self):
        """Click the search button."""
        boton_consultar = self.wait_for_element(By.ID, "formPublica:buscarPorParteButton")
        if boton_consultar:
            boton_consultar.click()
            self.logger.info("Search button clicked successfully.")
        else:
            self.logger.error("Could not click search button.")

    def navigate_and_extract_cases(self) -> int:
        """
        Navigate through results pages and extract case details.
        
        Returns:
            int: Total number of cases extracted
        """
        total_cases = 0

        while True:
            try:
                # Wait for table to load
                table = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
                )
                
                total_cases += self._process_table_rows()

                # Try to navigate to next page
                if not self._click_next_page():
                    break

            except Exception as e:
                self.logger.error(f"Error processing table: {e}")
                break

        self.logger.info(f"Total cases extracted: {total_cases}")
        return total_cases

    def _process_table_rows(self) -> int:
        """
        Process each row in the table, extracting case details with robust error handling.
        
        Returns:
            int: Number of cases processed in current page
        """
        cases_processed = 0

        # Dynamic wait and re-finding of rows to handle potential staleness
        def get_table_rows():
            table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
            )
            return table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header

        # Get initial rows
        rows = get_table_rows()

        for index in range(len(rows)):
            try:
                # Re-find rows and specific row to handle potential staleness
                current_rows = get_table_rows()
                
                if index >= len(current_rows):
                    self.logger.warning(f"Row index {index} is out of range. Skipping.")
                    break

                row = current_rows[index]

                # Use explicit wait and retry mechanism for view icon
                try:
                    view_icon = WebDriverWait(row, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "fa-eye"))
                    )
                    
                    # Use JavaScript click to mitigate staleness
                    self.driver.execute_script("arguments[0].click();", view_icon)
                except Exception as icon_error:
                    self.logger.error(f"Could not find or click view icon in row {index}: {icon_error}")
                    continue

                # Wait for case details page
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "col-xs-10"))
                )

                # Extract case number
                case_number = self._extract_case_number()
                if case_number:
                    cases_processed += 1
                    self.logger.info(f"Case {case_number} extracted successfully.")

                # Return to table with additional safeguards
                self._return_to_table()

            except Exception as e:
                self.logger.error(f"Error processing row {index}: {e}")
                
                # Additional recovery mechanism
                try:
                    # Try to return to table if we're stuck in a detail view
                    self._force_return_to_table()
                except Exception as recovery_error:
                    self.logger.error(f"Could not recover from error: {recovery_error}")
                    break

        return cases_processed

    def _extract_case_number(self) -> Optional[str]:
        """
        Extract case number from details page.
        
        Returns:
            Optional[str]: Case number or None if extraction fails
        """
        try:
            case_container = self.driver.find_element(By.CLASS_NAME, "col-xs-10")
            case_number = case_container.find_element(By.TAG_NAME, "span").text
            return case_number
        except Exception as e:
            self.logger.error(f"Error extracting case number: {e}")
            return None

    def _return_to_table(self):
        """Return to the results table from case details."""
        try:
            back_button = self.driver.find_element(By.CLASS_NAME, "btn-default")
            if back_button.is_displayed() and back_button.is_enabled():
                back_button.click()
                self.logger.info("Returned to results table successfully.")
                
                # Wait for table to reload
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
                )
        except Exception as e:
            self.logger.error(f"Error returning to table: {e}")

    def _force_return_to_table(self):
        """
        Forceful method to return to the results table using multiple strategies.
        """
        strategies = [
            lambda: self.driver.find_element(By.CLASS_NAME, "btn-default").click(),
            lambda: self.driver.execute_script("window.history.back()"),
            lambda: self.driver.get(self.driver.current_url)  # Reload current page
        ]

        for strategy in strategies:
            try:
                strategy()
                
                # Wait for table to reload
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
                )
                self.logger.info("Successfully returned to results table.")
                return
            except Exception as e:
                self.logger.warning(f"Strategy failed: {e}")

        raise Exception("Could not return to results table using any strategy.")

    def _click_next_page(self) -> bool:
        """
        Attempt to navigate to the next page of results.
        
        Returns:
            bool: True if next page exists and is clickable, False otherwise
        """
        try:
            next_button = self.driver.find_element(By.XPATH, '//*[@id="j_idt118:j_idt208:j_idt215"]')
            
            if next_button.is_displayed() and next_button.is_enabled():
                next_button.click()
                self.logger.info("Navigated to next page successfully.")
                return True
            else:
                self.logger.info("No more pages available.")
                return False
        except Exception:
            self.logger.info("Could not find next page button.")
            return False

    def run(self, search_term: str = "residuos"):
        """
        Main method to execute the entire scraping process.
        
        Args:
            search_term (str): Term to search in case details
        """
        try:
            # Setup driver
            self.setup_driver()

            # Perform search
            self.search_cases(search_term)

            # Navigate and extract cases
            self.navigate_and_extract_cases()

        except Exception as e:
            self.logger.error(f"Unexpected error during scraping: {e}")
        finally:
            # Always close the driver
            if self.driver:
                self.driver.quit()

def main():
    """Entry point for the web scraper."""
    scraper = WebScraper()
    scraper.run()

if __name__ == "__main__":
    main()