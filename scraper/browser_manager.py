from playwright.sync_api import sync_playwright
import requests
import subprocess
import time

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

class BrowserManager:
    def __init__(self, chrome_path=CHROME_PATH):
        self.chrome_path = chrome_path
        self.browser = None
        self.playwright = None
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self._setup_browser_with_instance()
        return self.browser
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def _setup_browser_with_instance(self):
        """Connect to an existing Chrome instance or start a new one with remote debugging enabled"""
        try:
            # Check if browser is already running with debugging port
            response = requests.get('http://localhost:9222/json/version', timeout=2)
            if response.status_code == 200:
                print('Connecting to existing Chrome instance')
                browser = self.playwright.chromium.connect_over_cdp(
                    endpoint_url='http://localhost:9222',
                    timeout=20000  # 20 second timeout for connection
                )
                return browser
        except requests.ConnectionError:
            print('No existing Chrome instance with debugging port found, starting a new one')
        
        # Start a new Chrome instance with remote debugging enabled
        subprocess.Popen(
            [
                self.chrome_path,
                '--remote-debugging-port=9222',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-blink-features=AutomationControlled',
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        # Wait for Chrome to start and be available
        for _ in range(10):
            try:
                response = requests.get('http://localhost:9222/json/version', timeout=2)
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        
        # Connect to the Chrome instance
        try:
            browser = self.playwright.chromium.connect_over_cdp(
                endpoint_url='http://localhost:9222',
                timeout=20000
            )
            return browser
        except Exception as e:
            print(f'Failed to connect to Chrome: {str(e)}')
            raise RuntimeError(
                'To start Chrome in Debug mode, you need to close all existing Chrome instances and try again.'
            ) 