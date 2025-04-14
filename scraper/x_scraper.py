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
        """Main scraping function that performs scrolling and tweet extraction"""
        # Directly get tweets by scrolling and parsing simultaneously
        tweets = self._scrape_tweets_while_scrolling(max_tweets=max_tweets)
        return tweets
    
    def _scrape_tweets_while_scrolling(self, max_tweets: int = 50, max_scroll_attempts: int = 20) -> List[Dict]:
        """Scroll through the feed and capture tweets as they appear"""
        all_tweets = []
        seen_tweet_urls = set()
        
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
            
            print(f"\nLoading content by scrolling until we find {max_tweets} tweets...")
            
            # Initial wait for any tweet to be visible
            try:
                print("Debug: Waiting for initial tweet elements...")
                page.wait_for_selector('article[role="article"]', timeout=30000)
                print("Debug: Initial tweets found")
            except Exception as e:
                print(f"Debug: Error finding initial tweets: {str(e)}")
                return []
            
            # Wait for the timeline section to be visible
            try:
                print("Debug: Waiting for timeline section...")
                page.wait_for_selector('section[role="region"][aria-labelledby^="accessible-list"]', timeout=30000)
                print("Debug: Timeline section found")
            except Exception as e:
                print(f"Debug: Error finding timeline section: {str(e)}")
                # Continue anyway as we might still find tweets
            
            # Extract tweets before any scrolling
            self._extract_visible_tweets(page, all_tweets, seen_tweet_urls, max_tweets)
            print(f"Debug: Extracted {len(all_tweets)} tweets before scrolling")
            
            previous_tweet_count = len(all_tweets)
            current_scroll = 0
            no_progress_count = 0  # Counter for consecutive scrolls with no new tweets
            
            # Scroll to load more tweets
            while len(all_tweets) < max_tweets and current_scroll < max_scroll_attempts:
                try:
                    print(f"Debug: Starting scroll {current_scroll+1}/{max_scroll_attempts} - Current tweets: {len(all_tweets)}/{max_tweets}")
                    
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
                        
                        # Try another scroll technique
                        page.mouse.move(500, 500)
                        page.mouse.wheel(0, 1000)
                        page.wait_for_timeout(2000)
                        
                        # Try space key as another method
                        page.keyboard.press("Space")
                        page.wait_for_timeout(2000)
                        
                        # Try to find and click any "Show more" or similar buttons
                        load_more_buttons = [
                            'button:has-text("Load more")', 
                            'button:has-text("Show more")',
                            'a:has-text("See more")',
                            'div[role="button"]:has-text("Show more")'
                        ]
                        
                        for button_selector in load_more_buttons:
                            try:
                                button = page.query_selector(button_selector)
                                if button:
                                    print(f"Debug: Found and clicking '{button_selector}'")
                                    button.click()
                                    page.wait_for_timeout(3000)
                                    break
                            except Exception as e:
                                print(f"Debug: Error clicking button: {str(e)}")
                                continue
                    
                    # Extract tweets after each scroll
                    self._extract_visible_tweets(page, all_tweets, seen_tweet_urls, max_tweets)
                    new_tweet_count = len(all_tweets)
                    print(f"Debug: Extracted {new_tweet_count} tweets after scroll {current_scroll+1}")
                    
                    # Check if we've made progress
                    if new_tweet_count > previous_tweet_count:
                        no_progress_count = 0  # Reset counter since we made progress
                    else:
                        no_progress_count += 1
                        if no_progress_count >= 3:
                            print("Debug: No new tweets found in the last 3 scrolls, may have reached the end")
                            break
                    
                    previous_tweet_count = new_tweet_count
                    
                    # Wait longer between scrolls to ensure content loads
                    page.wait_for_timeout(3000)
                    
                    current_scroll += 1
                    print(f"Debug: Completed scroll {current_scroll}/{max_scroll_attempts}")
                    
                except Exception as e:
                    print(f"Debug: Error during scrolling: {str(e)}")
                    page.wait_for_timeout(2000)
                    current_scroll += 1
            
            page.close()
            print(f"Debug: Scraped a total of {len(all_tweets)} tweets")
            
            return all_tweets[:max_tweets]
    
    def _extract_visible_tweets(self, page, all_tweets, seen_tweet_urls, max_tweets):
        """Extract data from all currently visible tweets"""
        # Extract tweet information
        tweet_elements = page.query_selector_all('article[role="article"]')
        print(f"Debug: Found {len(tweet_elements)} visible tweet elements")
        
        for tweet_element in tweet_elements:
            if len(all_tweets) >= max_tweets:
                return
                
            try:
                # Get tweet link to use as unique identifier
                time_element = tweet_element.query_selector('time')
                if not time_element:
                    continue
                    
                tweet_link = time_element.evaluate('(element) => element.parentElement.href')
                if tweet_link in seen_tweet_urls:
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
                
                seen_tweet_urls.add(tweet_link)
                all_tweets.append(tweet_data)
                print(f"Debug: Successfully added tweet {len(all_tweets)}")
                
            except Exception as e:
                print(f"Debug: Error extracting tweet details: {str(e)}")
    
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
                        
                        # Try another scroll technique
                        page.mouse.move(500, 500)
                        page.mouse.wheel(0, 1000)
                        page.wait_for_timeout(2000)
                        
                        # Try space key as another method
                        page.keyboard.press("Space")
                        page.wait_for_timeout(2000)
                        
                        # Try to find and click any "Show more" or similar buttons
                        load_more_buttons = [
                            'button:has-text("Load more")', 
                            'button:has-text("Show more")',
                            'a:has-text("See more")',
                            'div[role="button"]:has-text("Show more")'
                        ]
                        
                        for button_selector in load_more_buttons:
                            try:
                                button = page.query_selector(button_selector)
                                if button:
                                    print(f"Debug: Found and clicking '{button_selector}'")
                                    button.click()
                                    page.wait_for_timeout(3000)
                                    break
                            except Exception as e:
                                print(f"Debug: Error clicking button: {str(e)}")
                                continue
                    
                    # Wait longer between scrolls to ensure content loads
                    page.wait_for_timeout(3000)
                    
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
                        if (mainSection) {
                            return mainSection.outerHTML;
                        } else {
                            // Second fallback - get all articles directly
                            const articles = Array.from(document.querySelectorAll('article[role="article"]'));
                            if (articles.length > 0) {
                                return '<div>' + articles.map(a => a.outerHTML).join('') + '</div>';
                            } else {
                                return 'Timeline element not found';
                            }
                        }
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
                print("Debug: Falling back to saving full page HTML")
                # Force a full page screenshot first to ensure the page is fully rendered
                page.screenshot(path="raw_data/page_screenshot.png", full_page=True)
                page.wait_for_timeout(2000)
                
                # Try to get all articles first
                try:
                    articles = page.evaluate("""() => {
                        const articles = Array.from(document.querySelectorAll('article[role="article"]'));
                        return articles.length > 0 ? 
                            '<div>' + articles.map(a => a.outerHTML).join('') + '</div>' : null;
                    }""")
                    
                    if articles:
                        print(f"Debug: Found {articles.count('<article')} articles via fallback 1")
                        wrapped_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <title>X Feed Timeline (Fallback 1)</title>
                        </head>
                        <body>
                            {articles}
                        </body>
                        </html>
                        """
                        
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(wrapped_html)
                            
                        print(f"Debug: Saved articles HTML via fallback 1 to {file_path}")
                        return str(file_path)
                except Exception as e2:
                    print(f"Debug: Error in fallback 1: {str(e2)}")
                
                # Final fallback - save entire page
                feed_html = page.content()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(feed_html)
                print(f"Debug: Used final fallback to save full page HTML to {file_path}")
                
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
                    
                    # Check after adding each tweet if we've reached max_tweets
                    if len(tweets) >= max_tweets:
                        print(f"Debug: Reached max tweet limit of {max_tweets}")
                        break
                    
                except Exception as e:
                    print(f"Debug: Error extracting tweet details: {str(e)}")
            
            page.close()
            print(f"Debug: Parsed {len(tweets)} tweets from saved feed")
            
        return tweets[:max_tweets] 