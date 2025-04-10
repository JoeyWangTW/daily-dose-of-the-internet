from scraper.browser_manager import BrowserManager
from typing import List, Dict

class InstagramScraper:
    def __init__(self, user_data_dir: str = None):
        self.user_data_dir = user_data_dir
    
    def scrape_feed(self, max_posts: int = 50) -> List[Dict]:
        posts = []
        
        with BrowserManager() as browser:
            # Use the first context that's already open
            context = browser.contexts[0]
            print("\nDebug: Browser context created")
            
            # Create a new page in the existing context
            page = context.new_page()
            print("Debug: New page created")
            
            # Navigate to Instagram
            print("Debug: Navigating to Instagram...")
            page.goto('https://www.instagram.com', wait_until='networkidle')
            page.wait_for_timeout(3000)  # Longer wait for content to load
            print("Debug: Initial page load complete")
            
            print("\nStarting to collect Instagram posts...")
            
            # First try to find any posts
            post_count = page.evaluate("""() => {
                console.log('Looking for posts...');
                const articles = document.querySelectorAll('article');
                console.log('Found articles:', articles.length);
                
                // Log the HTML of the first article for debugging
                if (articles.length > 0) {
                    console.log('First article HTML structure:', articles[0].tagName);
                    console.log('First article children:', articles[0].children.length);
                }
                
                return articles.length;
            }""")
            
            print(f"Debug: JavaScript found {post_count} articles")
            
            # Try to parse a single post first
            first_post = page.evaluate("""() => {
                const articles = document.querySelectorAll('article');
                if (articles.length === 0) {
                    console.log('No articles found');
                    return null;
                }
                
                const article = articles[0];
                console.log('Processing first article');
                
                try {
                    // Get author info
                    const authorElement = article.querySelector('span._ap3a._aaco._aacw._aacx._aad7._aade');
                    console.log('Author element found:', !!authorElement);
                    
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
                    console.log('Text element found:', !!textElement);
                    
                    const text = textElement ? textElement.textContent.trim() : '';
                    
                    // Get timestamp and URL
                    const timeElement = article.querySelector('time');
                    console.log('Time element found:', !!timeElement);
                    
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
                            console.log('Like text found:', elem.textContent);
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
                    console.log('Image element found:', !!img);
                    
                    if (!img) {
                        // Try alternative selectors
                        img = article.querySelector('img.x5yr21d');
                        if (!img) {
                            img = article.querySelector('img.xpdipgo');
                        }
                    }
                    
                    const mediaUrl = img ? img.src : null;
                    
                    console.log('Successfully parsed first post');
                    
                    return {
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
                    };
                } catch (e) {
                    console.error('Error processing first post:', e);
                    return null;
                }
            }""")
            
            if first_post:
                print("Debug: Successfully parsed first post:")
                print(f"Author: {first_post['author']['name']}")
                print(f"Text: {first_post['text'][:50]}..." if first_post['text'] and len(first_post['text']) > 50 else f"Text: {first_post['text']}")
                print(f"URL: {first_post['url']}")
                print(f"Media URL: {first_post['media_url']}")
                print(f"Likes: {first_post['stats']['likes']}")
                
                posts.append(first_post)
                print("Debug: Added first post to collection")
            else:
                print("Debug: Failed to parse first post")
            
            # Only proceed with scrolling if we successfully parsed the first post
            if first_post:
                # Scroll to load more posts
                loaded_posts = set([first_post['url']] if first_post['url'] else set())
                attempts = 0
                max_attempts = max_posts * 2
                last_post_count = len(posts)
                
                while len(posts) < max_posts and attempts < max_attempts:
                    try:
                        # Scroll down
                        page.evaluate("""
                            window.scrollTo({
                                top: document.documentElement.scrollHeight,
                                behavior: 'smooth'
                            });
                        """)
                        
                        # Wait for new content
                        page.wait_for_timeout(3000)
                        
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
                        
                        print(f"Debug: Found {len(post_data)} posts in current scroll")
                        
                        # Add new posts
                        for post in post_data:
                            if post['url'] and post['url'] not in loaded_posts:
                                loaded_posts.add(post['url'])
                                posts.append(post)
                                print(f"Debug: Successfully added post {len(posts)}")
                                
                                if len(posts) >= max_posts:
                                    break
                        
                        # Check if we're still getting new posts
                        if len(posts) == last_post_count:
                            print("Debug: No new posts found in this scroll")
                            attempts += 1
                            if attempts >= 3:
                                print("Debug: Stopping as no new posts are being loaded")
                                break
                        else:
                            attempts = 0
                            last_post_count = len(posts)
                        
                    except Exception as e:
                        print(f"Debug: Error during scrolling: {str(e)}")
                        page.wait_for_timeout(2000)
                    
                    if len(posts) < max_posts:
                        print(f"Debug: Collected {len(posts)} posts so far, continuing to scroll...")
            
            page.close()
            print("Debug: Page closed")
            
            if len(posts) < max_posts:
                print(f"\nNote: Only found {len(posts)} unique posts after maximum attempts.")
        
        return posts[:max_posts] 