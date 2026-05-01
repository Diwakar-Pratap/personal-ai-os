import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Personal AI OS',
  description: 'Your private AI assistant with long-term memory and MCP tools',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
