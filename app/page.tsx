import { Feed } from '@/components/Feed';
import { loadFeedData } from '@/utils/feed';

export default function Home() {
  const feedItems = loadFeedData();

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          Daily Dose of the Internet
        </h1>
        <Feed items={feedItems} />
      </div>
    </main>
  );
}
