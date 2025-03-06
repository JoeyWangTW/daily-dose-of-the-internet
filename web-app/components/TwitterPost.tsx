import { TwitterPost as TwitterPostType } from '@/types/feed';
import Image from 'next/image';

export function TwitterPost({ post }: { post: TwitterPostType }) {
  return (
    <a href={post.url} target="_blank" rel="noopener noreferrer" 
       className="block p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow">
      <div className="flex items-start space-x-3">
        <div className="flex-grow">
          <div className="flex items-center space-x-2">
            <span className="text-lg font-semibold text-gray-900">{post.author.name}</span>
            <span className="text-sm text-gray-400">{post.author.handle}</span>
          </div>
          <p className="mt-2 text-gray-800">{post.text}</p>
          {post.media_url && (
            <div className="mt-3 relative rounded-lg overflow-hidden">
              <Image
                src={post.media_url}
                alt="Tweet media"
                width={400}
                height={300}
                className="object-cover"
              />
            </div>
          )}
          <div className="mt-2 text-sm text-gray-500">
            {new Date(post.timestamp).toLocaleDateString()}
          </div>
        </div>
      </div>
    </a>
  );
} 