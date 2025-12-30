/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  images: {
    unoptimized: true,
  },
  webpack: (config) => {
    // Resolve path aliases - use absolute path
    const projectRoot = path.resolve(__dirname);
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': projectRoot,
    };
    
    // Ensure proper module resolution
    if (!config.resolve.modules) {
      config.resolve.modules = [];
    }
    config.resolve.modules.push(projectRoot);
    
    return config;
  },
  // Ensure TypeScript paths are respected
  experimental: {
    // This helps with path resolution
  },
}

module.exports = nextConfig

