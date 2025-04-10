from scraper.browser_manager import BrowserManager
from typing import List, Dict
import time
import os
from pathlib import Path
from datetime import datetime

class XScraper:
    def __init__(self, user_data_dir: str = None):
        self.user_data_dir = user_data_dir
        # Create raw_data directory if it doesn't exist
        self.raw_data_dir = Path("raw_data")
        self.raw_data_dir.mkdir(exist_ok=True)
    
    def scrape_feed(self, max_tweets: int = 50) -> List[Dict]:
        """Main scraping function that performs both loading and parsing steps"""
        # Step 1: Load and save the feed
        html_file_path = self._load_and_save_feed()
        
        # Step 2: Parse the saved feed
        tweets = self._parse_saved_feed(html_file_path, max_tweets)
        
        return tweets
    
    def _load_and_save_feed(self, scroll_count: int = 3) -> str:
        """Step 1: Load the feed by scrolling and save the HTML content"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.raw_data_dir / f"x_feed_{timestamp}.html"
        
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
                    return ""
            
            print(f"\nLoading content by scrolling {scroll_count} times...")
            
            # Initial wait for any tweet to be visible
            try:
                print("Debug: Waiting for initial tweet elements...")
                page.wait_for_selector('article[role="article"]', timeout=30000)
                print("Debug: Initial tweets found")
            except Exception as e:
                print(f"Debug: Error finding initial tweets: {str(e)}")
                return ""
            
            # Wait for the timeline section to be visible
            try:
                print("Debug: Waiting for timeline section...")
                page.wait_for_selector('section[role="region"][aria-labelledby^="accessible-list"]', timeout=30000)
                print("Debug: Timeline section found")
            except Exception as e:
                print(f"Debug: Error finding timeline section: {str(e)}")
                # Continue anyway as we might still find tweets
            
            # Scroll to load more tweets
            for i in range(scroll_count):
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
                    
                    print(f"Debug: Completed scroll {i+1}/{scroll_count}")
                    
                except Exception as e:
                    print(f"Debug: Error during scrolling: {str(e)}")
                    page.wait_for_timeout(2000)
            
            # Extract and save only the timeline element
            try:
                print("Debug: Extracting timeline element...")
                timeline_html = page.evaluate("""() => {
                    // Look for the section with role="region" and aria-labelledby starting with "accessible-list"
                    const timeline = document.querySelector('section[role="region"][aria-labelledby^="accessible-list"]');
                    if (timeline) {
                        return timeline.outerHTML;
                    } else {
                        // Fallback if exact selector doesn't match
                        const mainSection = document.querySelector('div[data-testid="primaryColumn"] section');
                        return mainSection ? mainSection.outerHTML : 'Timeline element not found';
                    }
                }""")
                
                # Create a minimal HTML wrapper
                wrapped_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>X Feed Timeline</title>
                </head>
                <body>
                    {timeline_html}
                </body>
                </html>
                """
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(wrapped_html)
                    
                print(f"Debug: Saved timeline HTML to {file_path}")
            except Exception as e:
                print(f"Debug: Error extracting timeline element: {str(e)}")
                # Fallback to saving the entire page content
                feed_html = page.content()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(feed_html)
                print(f"Debug: Fallback to saving full page HTML to {file_path}")
                
            page.close()
            
            return str(file_path)
    
    def _parse_saved_feed(self, html_file_path: str, max_tweets: int = 50) -> List[Dict]:
        """Step 2: Parse the saved feed HTML to extract tweet information"""
        if not html_file_path or not os.path.exists(html_file_path):
            print(f"Error: File {html_file_path} not found")
            return []
            
        tweets = []
        print(f"\nParsing saved feed from {html_file_path}...")
        
        with BrowserManager() as browser:
            # Use the first context that's already open
            context = browser.contexts[0]
            
            # Create a new page in the existing context
            page = context.new_page()
            
            # Load the saved HTML file
            page.goto(f"file://{os.path.abspath(html_file_path)}", wait_until='domcontentloaded')
            print("Debug: Loaded saved HTML file")
            
            # Wait for the tweet elements to be accessible
            try:
                page.wait_for_selector('article[role="article"]', timeout=10000)
            except Exception as e:
                print(f"Debug: Error finding tweet elements in saved file: {str(e)}")
                return []
            
            # Extract tweet information
            tweet_elements = page.query_selector_all('article[role="article"]')
            print(f"Debug: Found {len(tweet_elements)} tweet elements in saved file")
            
            loaded_tweets = set()
            
            for tweet_element in tweet_elements:
                if len(tweets) >= max_tweets:
                    break
                    
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
                    
                except Exception as e:
                    print(f"Debug: Error extracting tweet details: {str(e)}")
            
            page.close()
            print(f"Debug: Parsed {len(tweets)} tweets from saved feed")
            
        return tweets[:max_tweets] 