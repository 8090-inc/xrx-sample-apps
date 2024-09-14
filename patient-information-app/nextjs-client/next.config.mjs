// next.config.mjs
/**
 * @type {import('next').NextConfig}
 */

import CopyPlugin from "copy-webpack-plugin";

const nextConfig = {
  output: "standalone",
  images: {
    domains: ["cdn.shopify.com"]
  },
  webpack: (config, {}) => {
    config.resolve.extensions.push(".ts", ".tsx");
    config.resolve.fallback = { fs: false };

    config.plugins.push(
      new CopyPlugin({
        patterns: [
          {
            from: "./node_modules/onnxruntime-web/dist/ort-wasm.wasm",
            to: "static/chunks/[name][ext]"
          },
          {
            from: "./node_modules/onnxruntime-web/dist/ort-wasm-simd.wasm",
            to: "static/chunks/[name][ext]"
          },
          {
            from: "node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js",
            to: "static/chunks/[name][ext]"
          },
          {
            from: "node_modules/@ricky0123/vad-web/dist/*.onnx",
            to: "static/chunks/[name][ext]"
          }
        ]
      })
    );

    return config;
  }
};

import { config as configDotenv } from "dotenv";

// Load environment variables from a specific path
configDotenv({ path: "../.env", override: true });

export default nextConfig;
