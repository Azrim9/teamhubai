import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 120000,
      gcTime: 600000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
