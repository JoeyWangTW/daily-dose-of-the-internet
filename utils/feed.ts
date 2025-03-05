import { FeedItem, TwitterPost, YouTubePost } from '@/types/feed';
import twitterData from '@/data/twitter_feed.json';
import youtubeData from '@/data/youtube_feed.json';

type RawTwitterPost = {
  author: {
    name: string;
    handle: string;
  };
  text: string;
  timestamp: string;
  url: string;
  media_url: string | null;
};

type RawYouTubePost = {
  title: string;
  channel: string;
  url: string;
  thumbnail: string;
  posted_time: string;
  views: string;
};

export function loadFeedData(): FeedItem[] {
  const twitterPosts: TwitterPost[] = (twitterData as RawTwitterPost[]).map(post => ({
    type: 'twitter',
    author: post.author,
    text: post.text,
    timestamp: post.timestamp,
    url: post.url,
    media_url: post.media_url,
  }));

  const youtubePosts: YouTubePost[] = (youtubeData as RawYouTubePost[]).map(post => ({
    type: 'youtube',
    title: post.title,
    channel: post.channel,
    url: post.url,
    thumbnail: post.thumbnail,
    posted_time: post.posted_time,
    views: post.views,
  }));

  // Combine and sort by timestamp/posted_time
  const allPosts = [...twitterPosts, ...youtubePosts].sort((a, b) => {
    const aTime = a.type === 'twitter' ? new Date(a.timestamp).getTime() : Date.now() - parseRelativeTime(a.posted_time);
    const bTime = b.type === 'twitter' ? new Date(b.timestamp).getTime() : Date.now() - parseRelativeTime(b.posted_time);
    return bTime - aTime;
  });

  return allPosts;
}

function parseRelativeTime(relativeTime: string): number {
  const number = parseInt(relativeTime);
  if (isNaN(number)) return 0;

  if (relativeTime.includes('year')) return number * 365 * 24 * 60 * 60 * 1000;
  if (relativeTime.includes('month')) return number * 30 * 24 * 60 * 60 * 1000;
  if (relativeTime.includes('week')) return number * 7 * 24 * 60 * 60 * 1000;
  if (relativeTime.includes('day')) return number * 24 * 60 * 60 * 1000;
  if (relativeTime.includes('hour')) return number * 60 * 60 * 1000;
  if (relativeTime.includes('minute')) return number * 60 * 1000;
  
  return 0;
} 