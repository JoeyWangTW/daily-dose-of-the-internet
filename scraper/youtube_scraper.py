from scraper.browser_manager import BrowserManager
from typing import List, Dict
import time

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