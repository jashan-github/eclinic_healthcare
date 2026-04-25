// // src/hooks/use-notifications.ts
// import {
//   useInfiniteQuery,
//   useMutation,
//   useQuery,
//   useQueryClient,
// } from "@tanstack/react-query";
// import {
//   fetchDoctorNotifications,
//   fetchUnreadNotificationCount,
//   markAllNotificationsAsRead,
//   markNotificationAsRead,
//   type NotificationsResponse,
//   type UnreadCountResponse,
// } from "@/services/notifications-service";
// import { toast } from "react-toastify";

// export const useDoctorNotifications = (
//   limit: number = 10,
//   role: string,
//   options?: { enabled?: boolean },
// ) => {
//   return useInfiniteQuery<NotificationsResponse, Error>({
//     queryKey: ["doctor-notifications"],
//     queryFn: ({ pageParam = 1 }) =>
//       fetchDoctorNotifications(pageParam as number, limit, role),
//     getNextPageParam: (lastPage) => {
//       const { current_page, total_pages } = lastPage.pagination;
//       return current_page < total_pages ? current_page + 1 : undefined;
//     },
//     initialPageParam: 1,
//     staleTime: 2 * 60 * 1000,
//     refetchOnWindowFocus: true,
//     refetchOnMount: true,
//     retry: 2,
//     enabled: options?.enabled !== false,
//   });
// };

// export function useMarkNotificationAsRead() {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: ({ id, role }: { id: string; role: string }) =>
//       markNotificationAsRead(id, role),

//     onMutate: async () => {
//       await queryClient.cancelQueries({ queryKey: ["doctor-notifications"] });
//       const previous = queryClient.getQueryData(["doctor-notifications"]);
//       return { previous };
//     },

//     onSettled: (_data, _error) => {
//       queryClient.invalidateQueries({
//         queryKey: ["doctor-notifications"],
//       });
//     },

//     onError: (_err, _vars, context) => {
//       if (context?.previous) {
//         queryClient.setQueryData(["doctor-notifications"], context.previous);
//       }
//       toast.error("Failed to mark notification as read");
//     },
//   });
// }

// export function useMarkAllNotificationsAsRead() {
//   const queryClient = useQueryClient();

//   return useMutation({
//     mutationFn: (role: string) => markAllNotificationsAsRead(role),

//     onSuccess: (_data) => {
//       queryClient.invalidateQueries({ queryKey: ["doctor-notifications"] });
//       toast.success("All notifications marked as read");
//     },

//     onError: () => {
//       toast.error("Failed to mark all notifications as read");
//     },
//   });
// }

// export const useUnreadNotificationCount = (
//   role: string,
//   options?: { enabled?: boolean },
// ) => {
//   const isEnabled =
//     options?.enabled !== false && (role === "doctor" || role === "patient");
//   return useQuery<UnreadCountResponse, Error>({
//     queryKey: ["unread-notification-count", role],
//     queryFn: () => fetchUnreadNotificationCount(role),
//     staleTime: 60 * 1000,
//     refetchInterval: 2 * 60 * 1000,
//     refetchOnWindowFocus: true,
//     retry: 2,

//     enabled: isEnabled,
//   });
// };

import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  fetchDoctorNotifications,
  fetchUnreadNotificationCount,
  markAllNotificationsAsRead,
  markNotificationAsRead,
  type NotificationsResponse,
  type UnreadCountResponse,
} from "@/services/notifications-service";
import { toast } from "react-toastify";

/* -------------------------------------------------------------------------- */
/*                              Notifications List                            */
/* -------------------------------------------------------------------------- */

export const useDoctorNotifications = (
  limit: number = 10,
  role: string,
  options?: { enabled?: boolean },
) => {
  return useInfiniteQuery<NotificationsResponse, Error>({
    queryKey: ["doctor-notifications", role, limit],
    queryFn: ({ pageParam = 1 }) =>
      fetchDoctorNotifications(pageParam as number, limit, role),
    getNextPageParam: (lastPage) => {
      const { current_page, total_pages } = lastPage.pagination;
      return current_page < total_pages ? current_page + 1 : undefined;
    },
    initialPageParam: 1,
    staleTime: 2 * 60 * 1000,
    refetchOnWindowFocus: true,
    retry: 2,
    enabled: options?.enabled !== false,
  });
};

/* -------------------------------------------------------------------------- */
/*                       Mark Single Notification As Read                      */
/* -------------------------------------------------------------------------- */

export function useMarkNotificationAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) =>
      markNotificationAsRead(id, role),

    // optimistic update
    onMutate: async ({ id, role }) => {
      await queryClient.cancelQueries({
        queryKey: ["doctor-notifications", role],
      });

      const previousNotifications = queryClient.getQueryData([
        "doctor-notifications",
        role,
      ]);
      const previousCount = queryClient.getQueryData([
        "unread-notification-count",
        role,
      ]);

      // update list
      queryClient.setQueryData(["doctor-notifications", role], (old: any) => {
        if (!old) return old;

        return {
          ...old,
          pages: old.pages.map((page: any) => ({
            ...page,
            notifications: page.notifications.map((n: any) =>
              n.id === id ? { ...n, is_read: true } : n,
            ),
          })),
        };
      });

      // update count
      queryClient.setQueryData(
        ["unread-notification-count", role],
        (old: any) =>
          old ? { unread_count: Math.max(0, old.unread_count - 1) } : old,
      );

      return { previousNotifications, previousCount };
    },

    onError: (_err, vars, context) => {
      if (context?.previousNotifications) {
        queryClient.setQueryData(
          ["doctor-notifications", vars.role],
          context.previousNotifications,
        );
      }
      if (context?.previousCount) {
        queryClient.setQueryData(
          ["unread-notification-count", vars.role],
          context.previousCount,
        );
      }
      toast.error("Failed to mark notification as read");
    },

    onSettled: (_data, _error, vars) => {
      queryClient.invalidateQueries({
        queryKey: ["doctor-notifications", vars.role],
      });
      queryClient.invalidateQueries({
        queryKey: ["unread-notification-count", vars.role],
      });
    },
  });
}

/* -------------------------------------------------------------------------- */
/*                       Mark ALL Notifications As Read                        */
/* -------------------------------------------------------------------------- */

export function useMarkAllNotificationsAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (role: string) => markAllNotificationsAsRead(role),

    onSuccess: (_data, role) => {
      // mark all as read in list
      queryClient.setQueryData(["doctor-notifications", role], (old: any) => {
        if (!old) return old;

        return {
          ...old,
          pages: old.pages.map((page: any) => ({
            ...page,
            notifications: page.notifications.map((n: any) => ({
              ...n,
              is_read: true,
            })),
          })),
        };
      });

      // force unread count to zero
      queryClient.setQueryData(["unread-notification-count", role], {
        unread_count: 0,
      });

      queryClient.invalidateQueries({
        queryKey: ["doctor-notifications", role],
      });
      queryClient.invalidateQueries({
        queryKey: ["unread-notification-count", role],
      });

      toast.success("All notifications marked as read");
    },

    onError: () => {
      toast.error("Failed to mark all notifications as read");
    },
  });
}

/* -------------------------------------------------------------------------- */
/*                            Unread Count Query                               */
/* -------------------------------------------------------------------------- */

export const useUnreadNotificationCount = (
  role: string,
  options?: { enabled?: boolean },
) => {
  const enabled =
    options?.enabled !== false && (role === "doctor" || role === "patient");

  return useQuery<UnreadCountResponse, Error>({
    queryKey: ["unread-notification-count", role],
    queryFn: () => fetchUnreadNotificationCount(role),
    staleTime: 60 * 1000,
    refetchOnWindowFocus: true,
    retry: 2,
    enabled,
  });
};
