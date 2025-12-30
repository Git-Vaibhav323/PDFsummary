/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  images: {
    unoptimized: true,
  },
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Resolve path aliases - use absolute path
    const projectRoot = path.resolve(__dirname);
    
    // Ensure resolve object exists
    if (!config.resolve) {
      config.resolve = {};
    }
    
    // Override alias configuration - ensure @ points to project root
    // This must be done before any module resolution
    const existingAlias = config.resolve.alias || {};
    config.resolve.alias = {
      ...existingAlias,
      '@': projectRoot,
    };
    
    // Ensure proper module resolution - add project root first
    if (!config.resolve.modules) {
      config.resolve.modules = [];
    }
    
    // Remove projectRoot if it exists, then add it at the beginning
    config.resolve.modules = config.resolve.modules.filter(m => m !== projectRoot);
    config.resolve.modules.unshift(projectRoot);
    
    // Ensure extensions include TypeScript files
    if (!config.resolve.extensions) {
      config.resolve.extensions = [];
    }
    const extensions = ['.tsx', '.ts', '.jsx', '.js', '.json'];
    extensions.forEach(ext => {
      if (!config.resolve.extensions.includes(ext)) {
        config.resolve.extensions.unshift(ext);
      }
    });
    
    return config;
  },
}

module.exports = nextConfig
