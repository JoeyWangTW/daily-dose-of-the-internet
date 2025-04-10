from scraper.browser_manager import BrowserManager
from typing import List, Dict
import time
import os
from pathlib import Path
from datetime import datetime

class YouTubeScraper:
    def __init__(self, user_data_dir: str = None):
        self.user_data_dir = user_data_dir
        # Create raw_data directory if it doesn't exist
        self.raw_data_dir = Path("raw_data")
        self.raw_data_dir.mkdir(exist_ok=True)
    
    def scrape_feed(self, max_videos: int = 50) -> List[Dict]:
        """Main scraping function that performs both loading and parsing steps"""
        # Step 1: Load and save the feed
        html_file_path = self._load_and_save_feed()
        
        # Step 2: Parse the saved feed
        videos = self._parse_saved_feed(html_file_path, max_videos)
        
        return videos
    
    def _load_and_save_feed(self, scroll_count: int = 5) -> str:
        """Step 1: Load the feed by scrolling and save the HTML content"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.raw_data_dir / f"youtube_feed_{timestamp}.html"
        
        with BrowserManager() as browser:
            # Use the first context that's already open
            context = browser.contexts[0]
            print("\nDebug: Browser context created")
            
            # Create a new page in the existing context
            page = context.new_page()
            print("Debug: New page created")
            
            # Navigate to YouTube home
            print("Debug: Navigating to YouTube home...")
            page.goto('https://www.youtube.com', wait_until='domcontentloaded')
            print("Debug: Initial page load complete")
            
            # Wait for the page to load and videos to appear
            try:
                print("Debug: Waiting for video elements...")
                page.wait_for_selector('ytd-rich-grid-media', timeout=30000)
                print("Debug: Video elements found")
            except Exception as e:
                print(f"Debug: Error finding video elements: {str(e)}")
                page.close()
                return ""
            
            print(f"\nLoading content by scrolling {scroll_count} times...")
            
            # Scroll to load more videos
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
            
            # Extract and save main content
            try:
                print("Debug: Extracting main content...")
                main_content = page.evaluate("""() => {
                    // Look for the main content element containing videos
                    const content = document.querySelector('ytd-rich-grid-renderer');
                    if (content) {
                        return content.outerHTML;
                    } else {
                        // Fallback if exact selector doesn't match
                        const mainSection = document.querySelector('#primary');
                        return mainSection ? mainSection.outerHTML : 'Main content element not found';
                    }
                }""")
                
                # Create a minimal HTML wrapper
                wrapped_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>YouTube Feed</title>
                </head>
                <body>
                    {main_content}
                </body>
                </html>
                """
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(wrapped_html)
                    
                print(f"Debug: Saved main content HTML to {file_path}")
            except Exception as e:
                print(f"Debug: Error extracting main content: {str(e)}")
                # Fallback to saving the entire page content
                feed_html = page.content()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(feed_html)
                print(f"Debug: Fallback to saving full page HTML to {file_path}")
                
            page.close()
            
            return str(file_path)
    
    def _parse_saved_feed(self, html_file_path: str, max_videos: int = 50) -> List[Dict]:
        """Step 2: Parse the saved feed HTML to extract video information"""
        if not html_file_path or not os.path.exists(html_file_path):
            print(f"Error: File {html_file_path} not found")
            return []
            
        videos = []
        print(f"\nParsing saved feed from {html_file_path}...")
        
        with BrowserManager() as browser:
            # Use the first context that's already open
            context = browser.contexts[0]
            
            # Create a new page in the existing context
            page = context.new_page()
            
            # Load the saved HTML file
            page.goto(f"file://{os.path.abspath(html_file_path)}", wait_until='domcontentloaded')
            print("Debug: Loaded saved HTML file")
            
            # Wait for the video elements to be accessible
            try:
                page.wait_for_selector('ytd-rich-grid-media', timeout=10000)
            except Exception as e:
                print(f"Debug: Error finding video elements in saved file: {str(e)}")
                return []
            
            # Extract video information
            video_elements = page.query_selector_all('ytd-rich-grid-media')
            print(f"Debug: Found {len(video_elements)} video elements in saved file")
            
            processed_urls = set()
            
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
                    
                    # Skip if we've already processed this URL or couldn't find it
                    if not video_url or video_url in processed_urls:
                        continue
                    
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
                    
                    processed_urls.add(video_url)
                    videos.append(video_data)
                    print(f"Debug: Successfully added video {len(videos)}: {title[:50]}...")
                    
                except Exception as e:
                    print(f"Debug: Error extracting video details: {str(e)}")
            
            page.close()
            print(f"Debug: Parsed {len(videos)} videos from saved feed")
            
        return videos[:max_videos] 