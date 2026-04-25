import { localStorageColorSchemeManager, MantineProvider } from "@mantine/core";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { useMemo } from "react";
import { createRoot } from "react-dom/client";
import { Flip, ToastContainer } from "react-toastify";
import { theme } from "./constants/theme";
import { useAuth } from "./context/auth/auth-context-utils";
import { AuthProvider } from "./context/auth/auth-provider";
import "./index.css";
import { routeTree } from "./routeTree.gen";

const colorSchemeManager = localStorageColorSchemeManager({
  key: "e-clinic-color-scheme",
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
    },
  },
});

export const InnerWrapper = () => {
  const auth = useAuth();
  const router = useMemo(
    () =>
      createRouter({
        routeTree,
        defaultPreload: false,
        context: { auth, queryClient },
        notFoundMode: "root",
      }),
    [auth],
  );

  return <RouterProvider router={router} />;
};

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <MantineProvider
        colorSchemeManager={colorSchemeManager}
        defaultColorScheme="light"
        theme={theme}
      >
        <InnerWrapper />
      </MantineProvider>
      <ToastContainer
        autoClose={1500}
        hideProgressBar
        newestOnTop={false}
        position="top-right"
        theme="colored"
        transition={Flip}
      />
    </AuthProvider>
    <ReactQueryDevtools initialIsOpen={false} />
  </QueryClientProvider>,
);
