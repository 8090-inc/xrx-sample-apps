// next.config.mjs
/**
 * @type {import('next').NextConfig}
 */

import CopyPlugin from "copy-webpack-plugin";

const nextConfig = {
  output: "standalone",
  webpack: (config, {}) => {
    config.resolve.extensions.push(".ts", ".tsx")
    config.resolve.fallback = { fs: false }

    config.plugins.push(
      new CopyPlugin({
        patterns: [
          {
            from: "node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js",
            to: "static/chunks/[name][ext]",
          },
          {
            from: "node_modules/@ricky0123/vad-web/dist/*.onnx",
            to: "static/chunks/[name][ext]",
          },
          {
            from: "node_modules/onnxruntime-web/dist/*.wasm",
            to: "static/chunks/[name][ext]",
          },
          // Copy JS files from lib/wasm/binding
          {
            from: 'node_modules/onnxruntime-web/lib/wasm/binding/*.js',
            to:'static/chunks/[name].mjs',
          },
          // Copy worker files
          {
            from: 'node_modules/onnxruntime-web/lib/wasm/binding/*.worker.js',
            to: 'static/chunks/[name].mjs',
          },
        ],
      })
    )

    return config
  },
  transpilePackages: ['react-xrx-client'],
};

import { config as configDotenv } from 'dotenv';

// Load environment variables from a specific path
configDotenv({ path: '../.env', override: true });

export default nextConfig;