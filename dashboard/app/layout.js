import "./globals.css";

export const metadata = {
  title: "AI Cloud Observability",
  description: "AI-Based Cloud Observability System - operations dashboard",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}