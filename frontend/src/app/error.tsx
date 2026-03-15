"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/Button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global UI error boundary triggered", error);
  }, [error]);

  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-50 antialiased font-sans">
        <main className="min-h-screen flex items-center justify-center p-6">
          <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 p-6 space-y-4">
            <h1 className="text-xl font-semibold text-slate-100">
              Something went wrong
            </h1>
            <p className="text-sm text-slate-400">
              The app detected an unexpected error. You can try recovering this
              screen without losing your session.
            </p>
            <div className="flex gap-3 pt-2">
              <Button onClick={reset}>Try Recovery</Button>
              <Button
                variant="secondary"
                onClick={() => window.location.reload()}
              >
                Reload App
              </Button>
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
