"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AuthProvider } from "@/hooks/useAuth";
import { SystemHealthGuard } from "@/components/system/SystemHealthGuard";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: (failureCount, error) => {
              const maybeHttpError = error as {
                response?: { status?: number };
              };
              const status = maybeHttpError.response?.status;
              if (status && [400, 401, 403, 404, 422].includes(status)) {
                return false;
              }
              return failureCount < 3;
            },
            retryDelay: (attemptIndex) =>
              Math.min(1000 * Math.pow(2, attemptIndex), 10000),
            refetchOnReconnect: true,
            refetchOnWindowFocus: true,
          },
          mutations: {
            retry: 0,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SystemHealthGuard />
        {children}
      </AuthProvider>
    </QueryClientProvider>
  );
}
