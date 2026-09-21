/** @type {import('next').NextConfig} */
const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  // This project lives inside a larger git repository; anchor Turbopack here.
  turbopack: {
    root: process.cwd(),
  },
  // Proxy API calls to the Python backend so the browser stays same-origin.
  async rewrites() {
    return [{ source: "/backend/:path*", destination: `${backendUrl}/:path*` }];
  },
};

export default nextConfig;