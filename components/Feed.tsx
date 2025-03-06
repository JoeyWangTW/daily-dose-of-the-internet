import { FeedItem } from '@/types/feed';
import { TwitterPost } from './TwitterPost';
import { YouTubePost } from './YouTubePost';
import { InstagramPost } from './InstagramPost';

export function Feed({ items }: { items: FeedItem[] }) {
  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        <div key={index}>
          {item.type === 'twitter' ? (
            <TwitterPost post={item} />
          ) : item.type === 'youtube' ? (
            <YouTubePost post={item} />
          ) : (
            <InstagramPost post={item} />
          )}
        </div>
      ))}
    </div>
  );
} 