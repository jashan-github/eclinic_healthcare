import { getMetaTitle } from "@/lib/utils";
import Home from "@/pages/home";
import { getFirstAllowedRoute } from "@/utils/permission-utils";
import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  beforeLoad: async ({ context }) => {
    const { isAuthenticated, user, permissions } = context.auth;

    if (!isAuthenticated || !user) {
      throw redirect({ to: "/auth/login" });
    }

    if (!user.is_profile_complete && user?.role === "doctor") {
      throw redirect({ to: "/app/create-profile" });
    }

    const firstRoute = getFirstAllowedRoute(user.role, permissions ?? []);
    console.log(firstRoute);

    throw redirect({ to: firstRoute });
  },
  component: Home,
  head: () => ({
    meta: [
      {
        title: getMetaTitle("Welcome"),
      },
    ],
  }),
});

// import { getMetaTitle } from '@/lib/utils'
// import Home from '@/pages/home'
// import { createFileRoute, redirect } from '@tanstack/react-router'

// export const Route = createFileRoute('/')({
//   beforeLoad: async ({ context }) => {
//     if (context.auth.isAuthenticated) {
//       console.log("context.auth.isDoctor", context.auth.isDoctor)
//       console.log("!context.auth.user?.is_completed", !context.auth.user?.is_completed)
//       if (context.auth.isDoctor && !context.auth.user?.is_completed) {
//         return redirect({ to: '/app/create-profile' })
//       }

//       return redirect({ to: '/app/appointments' })
//     } else {
//       throw redirect({ to: '/auth/login' })
//     }
//   },
//   component: Home,
//   head: () => ({
//     meta: [
//       {
//         title: getMetaTitle('Welcome')
//       }
//     ]
//   })
// })
