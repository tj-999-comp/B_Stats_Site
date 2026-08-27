/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  basePath: '/B_Stats_Site',
  transpilePackages: ['@bleague-stats/shared-ui', '@bleague-stats/supabase-client'],
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
