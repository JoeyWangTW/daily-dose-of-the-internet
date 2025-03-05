/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: [
      'pbs.twimg.com',
      'i.ytimg.com',
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