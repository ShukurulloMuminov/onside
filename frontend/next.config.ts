import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained .next/standalone build (minimal node_modules
  // subset + a server.js entrypoint) — much smaller Docker image than
  // shipping the full node_modules tree for `next start`.
  output: "standalone",
};

export default nextConfig;
