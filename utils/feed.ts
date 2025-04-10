import { FeedItem, TwitterPost, YouTubePost, InstagramPost } from '@/types/feed';

// Define empty default data
let twitterData: any[] = [];
let youtubeData: any[] = [];
let instagramData: any[] = [];

// Try individual imports
try {
  // @ts-ignore - Handle missing module
  twitterData = require('@/data/twitter_feed.json') || [];
} catch (e) {
  console.log('Twitter data not found');
}

try {
  // @ts-ignore - Handle missing module
  youtubeData = require('@/data/youtube_feed.json') || [];
} catch (e) {
  console.log('YouTube data not found');
}

try {
  // @ts-ignore - Handle missing module
  instagramData = require('@/data/instagram_feed.json') || [];
} catch (e) {
  console.log('Instagram data not found');
}

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

type RawInstagramPost = {
  author: {
    name: string;
    handle: string;
  };
  text: string;
  timestamp: string;
  url: string;
  media_url: string | null;
  stats: {
    likes?: string;
  };
};

function parseRelativeTime(timeStr: string): number {
  const now = Date.now();
  const units: { [key: string]: number } = {
    second: 1000,
    minute: 60 * 1000,
    hour: 60 * 60 * 1000,
    day: 24 * 60 * 60 * 1000,
    week: 7 * 24 * 60 * 60 * 1000,
    month: 30 * 24 * 60 * 60 * 1000,
    year: 365 * 24 * 60 * 60 * 1000,
  };

  const match = timeStr.match(/(\d+)\s+(\w+)/);
  if (!match) return 0;

  const [, count, unit] = match;
  const unitMs = units[unit.toLowerCase().replace(/s$/, '')] || 0;
  return parseInt(count) * unitMs;
}

export function loadFeedData(): FeedItem[] {
  const twitterPosts: TwitterPost[] = Array.isArray(twitterData) 
    ? (twitterData as RawTwitterPost[]).map(post => ({
        type: 'twitter',
        author: post.author,
        text: post.text,
        timestamp: post.timestamp,
        url: post.url,
        media_url: post.media_url,
      }))
    : [];

  const youtubePosts: YouTubePost[] = Array.isArray(youtubeData)
    ? (youtubeData as RawYouTubePost[]).map(post => ({
        type: 'youtube',
        title: post.title,
        channel: post.channel,
        url: post.url,
        thumbnail: post.thumbnail,
        posted_time: post.posted_time,
        views: post.views,
      }))
    : [];

  const instagramPosts: InstagramPost[] = Array.isArray(instagramData)
    ? (instagramData as RawInstagramPost[]).map(post => ({
        type: 'instagram',
        author: post.author,
        text: post.text,
        timestamp: post.timestamp,
        url: post.url,
        media_url: post.media_url,
        stats: post.stats,
      }))
    : [];

  // Combine and sort by timestamp/posted_time
  const allPosts = [...twitterPosts, ...youtubePosts, ...instagramPosts].sort((a, b) => {
    const aTime = a.type === 'youtube' ? 
      Date.now() - parseRelativeTime(a.posted_time) : 
      new Date(a.timestamp).getTime();
    const bTime = b.type === 'youtube' ? 
      Date.now() - parseRelativeTime(b.posted_time) : 
      new Date(b.timestamp).getTime();
    return bTime - aTime;
  });

  return allPosts;
} 