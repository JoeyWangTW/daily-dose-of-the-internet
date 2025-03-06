/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: [
      'pbs.twimg.com',
      'i.ytimg.com',
      'scontent-lga3-1.cdninstagram.com',
      'scontent-lga3-2.cdninstagram.com',
      'scontent-lga3-3.cdninstagram.com',
      'scontent-lga3-4.cdninstagram.com',
      'scontent-iad3-1.cdninstagram.com',
      'scontent-iad3-2.cdninstagram.com',
      'scontent.cdninstagram.com',
      'scontent.instagram.com',
      'instagram.com',
      'instagram.fnyc1-1.fna.fbcdn.net',
      'instagram.fnyc1-2.fna.fbcdn.net',
      'cdninstagram.com',
      'graph.instagram.com',
      'scontent-atl3-1.cdninstagram.com',
      'scontent-atl3-2.cdninstagram.com',
      'scontent-dfw5-1.cdninstagram.com',
      'scontent-dfw5-2.cdninstagram.com',
      'scontent-sea1-1.cdninstagram.com',
      'scontent-sea1-2.cdninstagram.com',
      'scontent-sjc3-1.cdninstagram.com',
      'scontent-sjc3-2.cdninstagram.com',
    ],
  },
  webpack: (config) => {
    config.module.rules.push({
      test: /\.json$/,
      type: 'json',
    });
    return config;
  },
};

export default nextConfig; 