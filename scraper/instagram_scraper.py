from scraper.browser_manager import BrowserManager
from typing import List, Dict
import time
import os
from pathlib import Path
from datetime import datetime
import random

class InstagramScraper:
    def __init__(self, user_data_dir: str = None):
        self.user_data_dir = user_data_dir
        # Create raw_data directory if it doesn't exist
        self.raw_data_dir = Path("raw_data")
        self.raw_data_dir.mkdir(exist_ok=True)
    
    def scrape_feed(self, max_posts: int = 50) -> List[Dict]:
        """Main scraping function that performs both loading and parsing steps"""
        # Step 1: Load and save the feed
        html_file_path = self._load_and_save_feed()
        
        # Step 2: Parse the saved feed
        posts = self._parse_saved_feed(html_file_path, max_posts)
        
        return posts
    
    def _load_and_save_feed(self, scroll_count: int = 3) -> str:
        """Step 1: Load the feed by scrolling and save the HTML content"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.raw_data_dir / f"instagram_feed_{timestamp}.html"
        
        with BrowserManager() as browser:
            # Use the first context that's already open
            context = browser.contexts[0]
            print("\nDebug: Browser context created")
            
            # Create a new page in the existing context
            page = context.new_page()
            print("Debug: New page created")
            
            # Navigate to Instagram
            print("Debug: Navigating to Instagram...")
            try:
                # Change wait_until to 'domcontentloaded' for faster initial load
                page.goto('https://www.instagram.com', wait_until='domcontentloaded')
                print("Debug: Initial page load complete")
                
                # Additional wait to ensure page is fully loaded
                page.wait_for_timeout(5000)
            except Exception as e:
                print(f"Debug: Error during initial page load: {str(e)}")
                # Try again with longer timeout
                try:
                    page.goto('https://www.instagram.com', wait_until='domcontentloaded', timeout=60000)
                    page.wait_for_timeout(5000)
                except Exception as e:
                    print(f"Debug: Error during retry page load: {str(e)}")
                    return ""
            
            print(f"\nLoading content by scrolling {scroll_count} times...")
            
            # Check for login status
            if page.url.startswith('https://www.instagram.com/accounts/login/'):
                print("\nPlease log in to Instagram in the browser window")
                print("Waiting for login (up to 2 minutes)...")
                try:
                    # Wait for navigation after login
                    page.wait_for_url('https://www.instagram.com/', timeout=120000)
                    print("Debug: Login detected and waited for redirect")
                    
                    # Additional wait after login
                    page.wait_for_timeout(5000)
                except Exception as e:
                    print(f"Debug: Error waiting for login redirect: {str(e)}")
                    return ""
            
            # Look for and dismiss any popups or dialogs
            try:
                # Check for and dismiss "Save Login Info" dialog
                save_info_button = page.query_selector('button:has-text("Not Now")')
                if save_info_button:
                    print("Debug: Found 'Not Now' button, clicking it")
                    save_info_button.click()
                    page.wait_for_timeout(2000)
                    
                # Check for and dismiss notifications dialog
                notifications_button = page.query_selector('button:has-text("Not Now")')
                if notifications_button:
                    print("Debug: Found notifications dialog, clicking 'Not Now'")
                    notifications_button.click()
                    page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Debug: Error handling dialogs: {str(e)}")
            
            # Wait for the feed to load
            try:
                print("Debug: Waiting for feed to load...")
                # Try multiple selectors for feed content
                feed_selectors = [
                    'article', 
                    'div[role="feed"]',
                    'div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x6s0dn4.x1oa3qoh.x1nhvcw1'
                ]
                
                feed_found = False
                for selector in feed_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=10000)
                        print(f"Debug: Feed found with selector: {selector}")
                        feed_found = True
                        break
                    except Exception:
                        continue
                
                if not feed_found:
                    print("Debug: Could not find feed with standard selectors")
                    # Try to interact with the page to force content loading
                    page.mouse.move(300, 300)
                    page.mouse.wheel(0, 200)
                    page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Debug: Error waiting for feed: {str(e)}")
                # Continue anyway and try scrolling
            
            # Use robust scrolling technique
            for i in range(scroll_count):
                try:
                    print(f"Debug: Starting scroll {i+1}/{scroll_count}")
                    
                    # Get current height
                    previous_height = page.evaluate("""() => {
                        return document.documentElement.scrollHeight;
                    }""")
                    print(f"Debug: Current document height: {previous_height}")
                    
                    # Scroll using different techniques
                    scroll_techniques = [
                        # Regular scroll to bottom
                        """() => {
                            window.scrollTo({
                                top: document.documentElement.scrollHeight,
                                behavior: 'smooth'
                            });
                        }""",
                        # Scroll by a fixed amount
                        """() => {
                            window.scrollBy({
                                top: 1000,
                                behavior: 'smooth'
                            });
                        }""",
                        # Click-based scroll
                        """() => {
                            // Find bottom-most element and click near it
                            const articles = document.querySelectorAll('article');
                            if (articles.length > 0) {
                                const lastArticle = articles[articles.length - 1];
                                lastArticle.scrollIntoView({ behavior: 'smooth', block: 'end' });
                            }
                        }"""
                    ]
                    
                    # Try primary scroll method
                    page.evaluate(scroll_techniques[0])
                    page.wait_for_timeout(3000)
                    
                    # Check if scroll worked
                    new_height = page.evaluate("""() => {
                        return document.documentElement.scrollHeight;
                    }""")
                    print(f"Debug: New document height: {new_height}")
                    
                    # If primary method didn't work, try alternatives
                    if new_height <= previous_height:
                        print("Debug: Primary scroll didn't work, trying alternative methods")
                        # Try alternative scroll methods
                        page.evaluate(scroll_techniques[1])
                        page.wait_for_timeout(2000)
                        
                        # Try mouse wheel simulation
                        page.mouse.move(500, 500)
                        page.mouse.wheel(0, 500)
                        page.wait_for_timeout(2000)
                        
                        # Try space key press to scroll
                        page.keyboard.press("Space")
                        page.wait_for_timeout(2000)
                        
                        # Try finding and clicking "Load more" type buttons
                        load_more_buttons = [
                            'button:has-text("Load more")', 
                            'button:has-text("Show more")',
                            'a:has-text("See more")'
                        ]
                        
                        for button_selector in load_more_buttons:
                            try:
                                button = page.query_selector(button_selector)
                                if button:
                                    print(f"Debug: Found and clicking '{button_selector}'")
                                    button.click()
                                    page.wait_for_timeout(3000)
                                    break
                            except Exception:
                                continue
                    
                    # Check if we're at the end of the feed
                    end_indicators = [
                        'div:has-text("You\'re all caught up")',
                        'div:has-text("End of feed")',
                        'div:has-text("No more posts")'
                    ]
                    
                    for indicator in end_indicators:
                        if page.query_selector(indicator):
                            print(f"Debug: Found end of feed indicator: {indicator}")
                            break
                    
                    # Add random pause between scrolls
                    wait_time = random.uniform(1.5, 3.0)
                    page.wait_for_timeout(int(wait_time * 1000))
                    
                    print(f"Debug: Completed scroll {i+1}/{scroll_count}")
                    
                except Exception as e:
                    print(f"Debug: Error during scrolling: {str(e)}")
                    page.wait_for_timeout(2000)
            
            # Take a short break before extracting content
            page.wait_for_timeout(3000)
            
            # Extract and save only the timeline element
            try:
                print("Debug: Extracting timeline element...")
                timeline_selector = 'div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x6s0dn4.x1oa3qoh.x1nhvcw1'
                
                timeline_html = page.evaluate(f"""() => {{
                    // Look for the main timeline div
                    const timeline = document.querySelector('{timeline_selector}');
                    if (timeline) {{
                        console.log('Found main timeline div');
                        return timeline.outerHTML;
                    }} else {{
                        console.log('Main timeline div not found, trying fallbacks');
                        // Fallback if exact selector doesn't match
                        const mainTimeline = document.querySelector('main div[role="feed"]');
                        if (mainTimeline) {{
                            console.log('Found feed by role');
                            return mainTimeline.outerHTML;
                        }}
                        
                        // Second fallback - any div containing articles
                        console.log('Looking for divs containing articles');
                        const articles = document.querySelectorAll('article');
                        console.log('Found', articles.length, 'articles');
                        
                        if (articles.length > 0) {{
                            // Find common parent containing all or most articles
                            const articleParents = [];
                            articles.forEach(article => {{
                                let parent = article.parentElement;
                                let depth = 0;
                                while (parent && depth < 5) {{
                                    articleParents.push(parent);
                                    parent = parent.parentElement;
                                    depth++;
                                }}
                            }});
                            
                            // Count occurrences of each parent to find the most common one
                            const parentCounts = {{}};
                            articleParents.forEach(parent => {{
                                const key = parent.tagName + '-' + (parent.id || '') + '-' + (parent.className || '');
                                parentCounts[key] = (parentCounts[key] || 0) + 1;
                            }});
                            
                            // Find the most common parent
                            let maxCount = 0;
                            let mostCommonParentKey = '';
                            for (const key in parentCounts) {{
                                if (parentCounts[key] > maxCount) {{
                                    maxCount = parentCounts[key];
                                    mostCommonParentKey = key;
                                }}
                            }}
                            
                            console.log('Most common parent found with', maxCount, 'occurrences');
                            
                            // Get all elements and find the one matching the most common key
                            const allElements = document.querySelectorAll('*');
                            for (const element of allElements) {{
                                const key = element.tagName + '-' + (element.id || '') + '-' + (element.className || '');
                                if (key === mostCommonParentKey) {{
                                    console.log('Found most common parent element');
                                    return element.outerHTML;
                                }}
                            }}
                        }}
                        
                        // Final fallback - just get the main content area
                        console.log('Using final fallback - main element');
                        const main = document.querySelector('main');
                        return main ? main.outerHTML : 'Timeline element not found, saving articles individually';
                    }}
                }}""")
                
                # Create a minimal HTML wrapper
                wrapped_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Instagram Feed Timeline</title>
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
    
    def _parse_saved_feed(self, html_file_path: str, max_posts: int = 50) -> List[Dict]:
        """Step 2: Parse the saved feed HTML to extract post information"""
        if not html_file_path or not os.path.exists(html_file_path):
            print(f"Error: File {html_file_path} not found")
            return []
            
        posts = []
        print(f"\nParsing saved feed from {html_file_path}...")
        
        with BrowserManager() as browser:
            # Use the first context that's already open
            context = browser.contexts[0]
            
            # Create a new page in the existing context
            page = context.new_page()
            
            # Load the saved HTML file
            page.goto(f"file://{os.path.abspath(html_file_path)}", wait_until='domcontentloaded')
            print("Debug: Loaded saved HTML file")
            
            # Wait for the post elements to be accessible
            try:
                page.wait_for_selector('article', timeout=10000)
            except Exception as e:
                print(f"Debug: Error finding article elements in saved file: {str(e)}")
                return []
            
            # Extract post information
            post_data = page.evaluate("""() => {
                const posts = [];
                document.querySelectorAll('article').forEach(article => {
                    try {
                        // Get author info
                        const authorElement = article.querySelector('span._ap3a._aaco._aacw._aacx._aad7._aade');
                        const authorName = authorElement ? authorElement.textContent.trim() : 'Unknown';
                        
                        // Try different selectors for profile image
                        let authorImg = article.querySelector('img[crossorigin="anonymous"]');
                        if (!authorImg) {
                            authorImg = article.querySelector('img[alt*="profile picture"]');
                        }
                        if (!authorImg) {
                            authorImg = article.querySelector('canvas.x1upo8f9');
                        }
                        
                        const verified = !!article.querySelector('svg[aria-label="Verified"]');
                        
                        // Get post text
                        const textElement = article.querySelector('span._ap3a._aaco._aacu._aacx._aad7._aade');
                        const text = textElement ? textElement.textContent.trim() : '';
                        
                        // Get timestamp and URL
                        const timeElement = article.querySelector('time');
                        const timestamp = timeElement ? timeElement.getAttribute('datetime') : null;
                        
                        // Try different approaches to get the post URL
                        let postLink = null;
                        if (timeElement && timeElement.parentElement) {
                            postLink = timeElement.parentElement.href;
                        }
                        if (!postLink) {
                            const linkElement = article.querySelector('a[href*="/p/"]');
                            if (linkElement) {
                                postLink = linkElement.href;
                            }
                        }
                        
                        // Get likes
                        let likes = null;
                        const likeElements = article.querySelectorAll('span[dir="auto"]');
                        for (const elem of likeElements) {
                            if (elem.textContent.includes('Liked by')) {
                                const match = elem.textContent.match(/Liked by ([^ ]+)/);
                                if (match) {
                                    likes = match[1];
                                } else {
                                    likes = elem.textContent;
                                }
                                break;
                            }
                        }
                        
                        // Get media
                        let img = article.querySelector('img[alt*="Photo by"]');
                        if (!img) {
                            // Try alternative selectors
                            img = article.querySelector('img.x5yr21d');
                            if (!img) {
                                img = article.querySelector('img.xpdipgo');
                            }
                        }
                        
                        const mediaUrl = img ? img.src : null;
                        
                        posts.push({
                            author: {
                                name: authorName,
                                handle: authorName,
                                verified: verified,
                                profile_image: authorImg ? authorImg.src : null
                            },
                            text: text,
                            timestamp: timestamp,
                            stats: { likes: likes },
                            url: postLink,
                            media_url: mediaUrl
                        });
                    } catch (e) {
                        console.error('Error processing post:', e);
                    }
                });
                return posts;
            }""")
            
            # Add unique posts to the collection
            loaded_urls = set()
            for post in post_data:
                if post['url'] and post['url'] not in loaded_urls:
                    loaded_urls.add(post['url'])
                    posts.append(post)
                    print(f"Debug: Successfully added post {len(posts)}")
                    
                    if len(posts) >= max_posts:
                        break
            
            page.close()
            print(f"Debug: Parsed {len(posts)} posts from saved feed")
            
        return posts[:max_posts] 