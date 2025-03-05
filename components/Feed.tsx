import { FeedItem } from '@/types/feed';
import { TwitterPost } from './TwitterPost';
import { YouTubePost } from './YouTubePost';

export function Feed({ items }: { items: FeedItem[] }) {
  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        <div key={index}>
          {item.type === 'twitter' ? (
            <TwitterPost post={item} />
          ) : (
            <YouTubePost post={item} />
          )}
        </div>
      ))}
    </div>
  );
} 