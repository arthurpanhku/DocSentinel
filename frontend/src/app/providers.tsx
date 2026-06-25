import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import type { ReactNode } from "react";
import { useState } from "react";

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: 1,
        staleTime: 15_000
      },
      mutations: {
        retry: 0
      }
    }
  });
}

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipPrimitive.Provider delayDuration={350}>
        {children}
      </TooltipPrimitive.Provider>
    </QueryClientProvider>
  );
}
