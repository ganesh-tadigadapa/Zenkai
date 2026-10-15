import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the workspace root to this app, so a stray lockfile in a parent
  // directory is not mistaken for the project root.
  turbopack: { root: __dirname },
};

export default nextConfig;
