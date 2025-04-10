from scraper.browser_manager import BrowserManager
from typing import List, Dict

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