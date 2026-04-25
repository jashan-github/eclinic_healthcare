import LoginPage from "@/pages/auth/login";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/auth/_auth-layout/login")({
  component: LoginPage,
  head: () => ({
    meta: [
      {
        title: "Login",
      },
    ],
  }),
});
