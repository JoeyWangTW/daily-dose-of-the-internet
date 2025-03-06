import { InstagramPost as InstagramPostType } from '@/types/feed';
import Image from 'next/image';

export function InstagramPost({ post }: { post: InstagramPostType }) {
  return (
    <a href={post.url} target="_blank" rel="noopener noreferrer" 
       className="block p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow">
      <div className="flex items-start space-x-3">
        <div className="flex-grow">
          <div className="flex items-center space-x-2">
            <span className="text-lg font-semibold text-gray-900">{post.author.name}</span>
            <span className="text-sm text-gray-400">@{post.author.handle}</span>
          </div>
          <p className="mt-2 text-gray-800">{post.text}</p>
          {post.media_url && (
            <div className="mt-3 relative rounded-lg overflow-hidden">
              <Image
                src={post.media_url}
                alt="Instagram post media"
                width={400}
                height={400}
                className="object-cover"
              />
            </div>
          )}
          <div className="mt-2 flex items-center justify-between text-sm text-gray-500">
            <span>{new Date(post.timestamp).toLocaleDateString()}</span>
            {post.stats.likes && (
              <span>{post.stats.likes} likes</span>
            )}
          </div>
        </div>
      </div>
    </a>
  );
} 