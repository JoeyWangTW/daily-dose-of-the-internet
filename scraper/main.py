import json
from pathlib import Path
from scraper.youtube_scraper import YouTubeScraper
from scraper.x_scraper import XScraper
from scraper.instagram_scraper import InstagramScraper

def main():
    # Define the path to save scraped data
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Get user input for platform choice
    print("\nAvailable options:")
    print("1. YouTube Feed")
    print("2. X (Twitter) Feed")
    print("3. Instagram Feed")
    
    while True:
        try:
            choice = int(input("\nEnter the number of your choice (1-3): "))
            if choice in [1, 2, 3]:
                if choice == 1:
                    platform = 'youtube_feed'
                elif choice == 2:
                    platform = 'x'
                else:
                    platform = 'instagram'
                break
            print("Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number (1-3).")
    
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
    
    elif platform == 'x':
        # Scrape Twitter feed
        x_scraper = XScraper()
        tweets = x_scraper.scrape_feed(max_tweets=count)
        
        # Save Twitter data
        with open(output_dir / "twitter_feed.json", "w", encoding="utf-8") as f:
            json.dump(tweets, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(tweets)} tweets to {output_dir / 'twitter_feed.json'}")
    
    else:  # platform == 'instagram'
        # Scrape Instagram feed
        instagram_scraper = InstagramScraper()
        posts = instagram_scraper.scrape_feed(max_posts=count)
        
        # Save Instagram data
        with open(output_dir / "instagram_feed.json", "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(posts)} Instagram posts to {output_dir / 'instagram_feed.json'}")

if __name__ == "__main__":
    main() 