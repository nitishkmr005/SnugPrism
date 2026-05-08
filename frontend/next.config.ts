import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Allow the backend Railway URL as an image source if needed
  images: {
    remotePatterns: [],
  },
}

export default nextConfig
