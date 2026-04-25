import AppLayout from "@/layouts/app-layout";
import { getMetaTitle } from "@/lib/utils";
import { createFileRoute, redirect } from "@tanstack/react-router";
import type { UserRoleType } from "@/utils/user-role";
// import { AUTH_TOKEN_KEY } from '@/constants'

export const Route = createFileRoute("/app/_app-layout")({
  beforeLoad: async ({ context, location }) => {
    // Allow patient-profile access without auth for development/testing
    // TODO: Remove this exception when ready for production
    // if (location.pathname === '/app/patient-profile') {
    //   // Set mock token and authentication for patient profile access
    //   if (!context.auth.isAuthenticated) {
    //     const mockToken = 'mock-patient-token-for-development'
    //     localStorage.setItem(AUTH_TOKEN_KEY, mockToken)
    //     localStorage.setItem('role', 'Patient') // Set role in localStorage for sidebar
    //     context.auth.setIsAuthenticated(true)
    //     context.auth.setUser({
    //       id: 'patient-mock',
    //       name: 'Mock Patient',
    //       email: 'patient@example.com',
    //       role: 'Patient'
    //     } as any)
    //   }
    //   return
    // }
    if (!navigator.onLine) {
      return;
    }

    if (sessionStorage.getItem("network-redirected") === "true") {
      return;
    }
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/auth/login",
        search: {
          redirect: location.href,
        },
      });
    }

    // Check if profile is complete for non-admin users
    // Skip this check if already on create-profile page to avoid redirect loop
    if (location.pathname !== "/app/create-profile") {
      const user = context.auth.user;
      if (!user) return;

      const roleFromStorage = localStorage.getItem("role");
      const userRole = (user.role ||
        roleFromStorage ||
        "doctor") as UserRoleType;

      // const isAdmin =
      //   userRole === 'super_admin' ||
      //   userRole === 'clinic_admin' ||
      //   userRole === 'admin'

      if (userRole === "doctor" && !user.is_profile_complete) {
        throw redirect({ to: "/app/create-profile" });
      }
    }
  },
  component: AppLayout,
  head: () => ({
    meta: [
      {
        title: getMetaTitle("Home"),
      },
    ],
  }),
});
