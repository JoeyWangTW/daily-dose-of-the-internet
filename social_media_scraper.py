from playwright.sync_api import sync_playwright
import time
import json
from typing import List, Dict, Optional
import os
import subprocess
import requests
from pathlib import Path

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

class YouTubeScraper:
    def __init__(self, user_data_dir: str = None):
        self.user_data_dir = user_data_dir
    
    def scrape_feed(self, max_videos: int = 50) -> List[Dict]:
        videos = []
        
        with BrowserManager() as browser:
            # Use the first context that's already open
            context = browser.contexts[0]
            
            # Create a new page in the existing context
            page = context.new_page()
            page.goto('https://www.youtube.com')
            
            # Wait for the page to load and videos to appear
            page.wait_for_selector('ytd-rich-grid-media', timeout=10000)
            page.wait_for_load_state('networkidle')
            
            # Scroll to load more videos
            for _ in range(min(max_videos // 10 + 1, 6)):  # Scroll more times to ensure we get enough videos
                try:
                    # Scroll and wait for new content
                    page.evaluate("""
                        window.scrollBy({
                            top: window.innerHeight,
                            behavior: 'smooth'
                        });
                    """)
                    page.wait_for_timeout(2000)  # Wait for content to load
                    
                    # Check if we have enough videos
                    current_videos = page.query_selector_all('ytd-rich-grid-media')
                    if len(current_videos) >= max_videos:
                        break
                        
                except Exception as e:
                    print(f"Scrolling error: {str(e)}")
                    time.sleep(1)
            
            # Extract video information
            video_elements = page.query_selector_all('ytd-rich-grid-media')
            print(f"\nFound {len(video_elements)} videos")
            
            for i, video_element in enumerate(video_elements):
                if i >= max_videos:
                    break
                
                try:
                    # Get video URL and ID from the thumbnail link
                    video_url = None
                    video_id = None
                    
                    # Try getting URL from thumbnail first
                    thumbnail_link = video_element.query_selector('#thumbnail[href]')
                    if thumbnail_link:
                        href = thumbnail_link.get_attribute('href')
                        if href:
                            video_url = f'https://www.youtube.com{href}' if not href.startswith('http') else href
                            # Extract video ID from href
                            if 'v=' in href:
                                video_id = href.split('v=')[-1].split('&')[0]
                    
                    # If not found, try getting from title
                    if not video_url:
                        title_link = video_element.query_selector('#video-title[href]')
                        if title_link:
                            href = title_link.get_attribute('href')
                            if href:
                                video_url = f'https://www.youtube.com{href}' if not href.startswith('http') else href
                                if 'v=' in href:
                                    video_id = href.split('v=')[-1].split('&')[0]
                    
                    # Extract video details
                    title_element = video_element.query_selector('#video-title')
                    title = title_element.text_content().strip() if title_element else "Unknown Title"
                    
                    # Get channel info with more specific selector
                    channel_element = video_element.query_selector('#channel-name a')
                    channel = channel_element.text_content().strip() if channel_element else "Unknown Channel"
                    
                    # Get metadata with more specific selectors
                    metadata_spans = video_element.query_selector_all('#metadata-line span')
                    views = "Unknown Views"
                    posted_time = "Unknown Time"
                    
                    if len(metadata_spans) >= 2:
                        views = metadata_spans[0].text_content().strip()
                        posted_time = metadata_spans[1].text_content().strip()
                    
                    # Get high quality thumbnail URL
                    thumbnail_url = None
                    if video_id:
                        thumbnail_url = f'https://i.ytimg.com/vi/{video_id}/hq720.jpg'
                    else:
                        # Try getting from img element as fallback
                        thumbnail_img = video_element.query_selector('#thumbnail img[src]')
                        if thumbnail_img:
                            thumbnail_url = thumbnail_img.get_attribute('src')
                    
                    video_data = {
                        'title': title,
                        'url': video_url,
                        'channel': channel,
                        'views': views,
                        'posted_time': posted_time,
                        'thumbnail': thumbnail_url,
                        'video_id': video_id
                    }
                    
                    videos.append(video_data)
                    print(f"Processed video {i+1}/{max_videos}: {title[:50]}...")
                    
                except Exception as e:
                    print(f"Error extracting video {i}: {str(e)}")
            
            page.close()
        
        return videos

class XScraper:
    def __init__(self, user_data_dir: str = None):
        self.user_data_dir = user_data_dir
    
    def scrape_feed(self, max_tweets: int = 50) -> List[Dict]:
        tweets = []
        
        with BrowserManager() as browser:
            # Use the first context that's already open
            context = browser.contexts[0]
            print("\nDebug: Browser context created")
            
            # Create a new page in the existing context
            page = context.new_page()
            print("Debug: New page created")
            
            # Navigate to Twitter with a shorter timeout for initial load
            print("Debug: Navigating to Twitter home...")
            page.goto('https://twitter.com/home', wait_until='domcontentloaded')
            print("Debug: Initial page load complete")
            
            # Check if we need to log in
            if page.url.startswith('https://twitter.com/i/flow/login'):
                print("\nPlease log in to X (Twitter) in the browser window")
                print("Waiting for login (up to 2 minutes)...")
                page.wait_for_url('https://twitter.com/home', timeout=120000)
                print("Debug: Login page detected and waited for redirect")
                
                # Wait for the feed to be visible after login
                print("Debug: Waiting for feed to load after login...")
                try:
                    page.wait_for_selector('article[role="article"]', timeout=30000)
                    print("Debug: Feed loaded successfully")
                except Exception as e:
                    print(f"Debug: Error waiting for feed: {str(e)}")
                    return []
            
            print("\nStarting to collect tweets...")
            
            # Initial wait for any tweet to be visible
            try:
                print("Debug: Waiting for initial tweet elements...")
                page.wait_for_selector('article[role="article"]', timeout=30000)
                print("Debug: Initial tweets found")
            except Exception as e:
                print(f"Debug: Error finding initial tweets: {str(e)}")
                return []
            
            # Scroll to load more tweets with better handling
            loaded_tweets = set()
            attempts = 0
            max_attempts = max_tweets * 2  # Allow more attempts to find unique tweets
            last_tweet_count = 0
            
            while len(tweets) < max_tweets and attempts < max_attempts:
                try:
                    # Get current scroll position
                    current_position = page.evaluate("""
                        window.pageYOffset || document.documentElement.scrollTop
                    """)
                    print(f"Debug: Current scroll position: {current_position}")
                    
                    # Scroll down
                    page.evaluate("""
                        window.scrollTo({
                            top: document.documentElement.scrollHeight,
                            behavior: 'smooth'
                        });
                    """)
                    
                    # Wait for new content
                    page.wait_for_timeout(3000)
                    
                    # Check if we've actually scrolled
                    new_position = page.evaluate("""
                        window.pageYOffset || document.documentElement.scrollTop
                    """)
                    print(f"Debug: New scroll position: {new_position}")
                    print(f"Debug: Scroll difference: {new_position - current_position}")
                    
                    if new_position <= current_position:
                        print("Debug: No scroll movement detected, trying alternative scroll")
                        # Try an alternative scroll method
                        page.evaluate("""
                            window.scrollBy({
                                top: 1000,
                                behavior: 'smooth'
                            });
                        """)
                        page.wait_for_timeout(2000)
                    
                    # Extract tweet information
                    tweet_elements = page.query_selector_all('article[role="article"]')
                    print(f"Debug: Found {len(tweet_elements)} tweet elements")
                    
                    # Check if we're still getting new tweets
                    if len(tweet_elements) == last_tweet_count:
                        print("Debug: No new tweets found in this scroll")
                        attempts += 1
                        if attempts >= 3:  # If we haven't found new tweets in 3 attempts
                            print("Debug: Stopping as no new tweets are being loaded")
                            break
                    else:
                        attempts = 0  # Reset attempts if we found new tweets
                        last_tweet_count = len(tweet_elements)
                    
                    for tweet_element in tweet_elements:
                        try:
                            # Get tweet link to use as unique identifier
                            time_element = tweet_element.query_selector('time')
                            if not time_element:
                                continue
                                
                            tweet_link = time_element.evaluate('(element) => element.parentElement.href')
                            if tweet_link in loaded_tweets:
                                continue
                            
                            # Extract tweet details using the correct selectors
                            # Author name and handle are in specific divs with dir="ltr"
                            author_element = tweet_element.query_selector('[data-testid="User-Name"]')
                            author_info = {
                                'name': "",
                                'handle': ""
                            }
                            
                            if author_element:
                                # Get author name from the first div[dir="ltr"] containing the name
                                name_element = author_element.query_selector('div.css-175oi2r.r-1awozwy.r-18u37iz.r-1wbh5a2 div[dir="ltr"]')
                                if name_element:
                                    author_info['name'] = name_element.text_content().strip()
                                
                                # Get handle from the subsequent div[dir="ltr"]
                                handle_element = author_element.query_selector('div.css-175oi2r.r-1d09ksm div[dir="ltr"]')
                                if handle_element:
                                    author_info['handle'] = handle_element.text_content().strip()
                            
                            # Tweet text is in the tweetText element
                            text_element = tweet_element.query_selector('[data-testid="tweetText"]')
                            text = text_element.text_content().strip() if text_element else ""
                            
                            print(f"Debug: Processing tweet by {author_info['name']} ({author_info['handle']})")
                            
                            # Get timestamp from time element
                            time_element = tweet_element.query_selector('time')
                            timestamp = time_element.get_attribute('datetime') if time_element else None
                            
                            # Get tweet stats with updated selectors
                            stats = {}
                            
                            # Get reply count
                            reply_element = tweet_element.query_selector('[data-testid="reply"]')
                            if reply_element:
                                reply_count = reply_element.query_selector('span[data-testid="app-text-transition-container"]')
                                stats['reply'] = reply_count.text_content().strip() if reply_count else "0"
                            
                            # Get retweet count
                            retweet_element = tweet_element.query_selector('[data-testid="retweet"]')
                            if retweet_element:
                                retweet_count = retweet_element.query_selector('span[data-testid="app-text-transition-container"]')
                                stats['retweet'] = retweet_count.text_content().strip() if retweet_count else "0"
                            
                            # Get like count
                            like_element = tweet_element.query_selector('[data-testid="like"]')
                            if like_element:
                                like_count = like_element.query_selector('span[data-testid="app-text-transition-container"]')
                                stats['like'] = like_count.text_content().strip() if like_count else "0"
                            
                            # Get view count
                            view_element = tweet_element.query_selector('a[aria-label*="views"]')
                            if view_element:
                                view_count = view_element.query_selector('span[data-testid="app-text-transition-container"]')
                                stats['views'] = view_count.text_content().strip() if view_count else "0"
                            
                            # Get media content if available
                            media_url = None
                            media_container = tweet_element.query_selector('[data-testid="tweetPhoto"]')
                            if media_container:
                                img_element = media_container.query_selector('img')
                                if img_element:
                                    media_url = img_element.get_attribute('src')
                            else:
                                # Check for video content
                                video_container = tweet_element.query_selector('video')
                                if video_container:
                                    media_url = video_container.get_attribute('poster')
                            
                            tweet_data = {
                                'author': author_info,
                                'text': text,
                                'timestamp': timestamp,
                                'stats': stats,
                                'url': tweet_link,
                                'media_url': media_url
                            }
                            
                            loaded_tweets.add(tweet_link)
                            tweets.append(tweet_data)
                            print(f"Debug: Successfully added tweet {len(tweets)}")
                            
                            if len(tweets) >= max_tweets:
                                break
                                
                        except Exception as e:
                            print(f"Debug: Error extracting tweet details: {str(e)}")
                    
                except Exception as e:
                    print(f"Debug: Error during scrolling: {str(e)}")
                    page.wait_for_timeout(2000)
                
                if len(tweets) < max_tweets:
                    print(f"Debug: Collected {len(tweets)} tweets so far, continuing to scroll...")
            
            page.close()
            print("Debug: Page closed")
            
            if len(tweets) < max_tweets:
                print(f"\nNote: Only found {len(tweets)} unique tweets after maximum attempts.")
            
        return tweets[:max_tweets]

def main():
    # Define the path to save scraped data
    output_dir = Path("scraped_data")
    output_dir.mkdir(exist_ok=True)
    
    # Get user input for platform choice
    print("\nAvailable options:")
    print("1. YouTube Feed")
    print("2. X (Twitter) Feed")
    
    while True:
        try:
            choice = int(input("\nEnter the number of your choice (1-2): "))
            if choice in [1, 2]:
                platform = 'youtube_feed' if choice == 1 else 'x'
                break
            print("Invalid choice. Please enter 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter a number (1 or 2).")
    
    # Get user input for content count for feed scraping
    MAX_ITEMS = 100
    while True:
        try:
            count = int(input(f"How many items would you like to scrape? (max {MAX_ITEMS}): "))
            if 0 < count <= MAX_ITEMS:
                break
            elif count <= 0:
                print("Please enter a positive number.")
            else:
                print(f"Please enter a number not exceeding {MAX_ITEMS}.")
        except ValueError:
            print("Please enter a valid number.")
    
    if platform == 'youtube_feed':
        # Scrape YouTube feed
        youtube_scraper = YouTubeScraper()
        youtube_videos = youtube_scraper.scrape_feed(max_videos=count)
        
        # Save YouTube data
        with open(output_dir / "youtube_feed.json", "w", encoding="utf-8") as f:
            json.dump(youtube_videos, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(youtube_videos)} YouTube videos to {output_dir / 'youtube_feed.json'}")
    
    else:  # platform == 'x'
        # Scrape Twitter feed
        x_scraper = XScraper()
        tweets = x_scraper.scrape_feed(max_tweets=count)
        
        # Save Twitter data
        with open(output_dir / "twitter_feed.json", "w", encoding="utf-8") as f:
            json.dump(tweets, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(tweets)} tweets to {output_dir / 'twitter_feed.json'}")

if __name__ == "__main__":
    main() 