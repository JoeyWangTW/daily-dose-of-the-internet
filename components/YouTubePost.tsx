"use client";

import { YouTubePost as YouTubePostType } from '@/types/feed';
import Image from 'next/image';
import { useState } from 'react';
import { YouTubeModal } from './YouTubeModal';

export function YouTubePost({ post }: { post: YouTubePostType }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const videoId = new URL(post.url).searchParams.get('v');

  return (
    <div className="block p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow">
      <div className="space-y-3">
        <button 
          onClick={() => setIsModalOpen(true)}
          className="relative w-full rounded-lg overflow-hidden aspect-video cursor-pointer group"
        >
          <Image
            src={post.thumbnail}
            alt={post.title}
            fill
            className="object-cover transition-transform group-hover:scale-105"
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-16 h-12 bg-red-600 rounded-lg flex items-center justify-center opacity-90 group-hover:opacity-100 transition-opacity">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>
        </button>
        <div>
          <h3 className="font-medium text-gray-900 line-clamp-2">{post.title}</h3>
          <p className="mt-1 text-sm text-gray-500">{post.channel}</p>
          <div className="mt-1 text-sm text-gray-500 flex items-center space-x-2">
            <span>{post.views}</span>
            <span>•</span>
            <span>{post.posted_time}</span>
          </div>
        </div>
      </div>
      {videoId && (
        <YouTubeModal
          videoId={videoId}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </div>
  );
} 