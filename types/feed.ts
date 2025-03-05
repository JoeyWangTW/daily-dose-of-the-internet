export type TwitterPost = {
  type: 'twitter';
  author: {
    name: string;
    handle: string;
  };
  text: string;
  timestamp: string;
  url: string;
  media_url: string | null;
};

export type YouTubePost = {
  type: 'youtube';
  title: string;
  channel: string;
  url: string;
  thumbnail: string;
  posted_time: string;
  views: string;
};

export type FeedItem = TwitterPost | YouTubePost; 