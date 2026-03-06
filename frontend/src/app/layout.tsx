import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'BBA Command OS',
  description: 'BBA Services Entrepreneur Command OS Powered by The Noble Savage',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-slate-950 text-slate-50 antialiased font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
