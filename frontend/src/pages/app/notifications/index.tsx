import type { FC, ReactElement } from "react";
import {
  useDoctorNotifications,
  useMarkAllNotificationsAsRead,
  useMarkNotificationAsRead,
  useUnreadNotificationCount,
} from "@/hooks/use-notifications";
import { ScrollArea, Text, Button } from "@mantine/core";
import { CheckIcon, XCircleIcon } from "@phosphor-icons/react";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "react-toastify";
import RequestDialog from "@/components/e-clinic/doctor/requests/request-dialog";
import type { NotificationItem } from "@/services/notifications-service"; // adjust path if needed
import {
  useAcceptRequest,
  useRejectRequest,
} from "@/features/app/requests/hooks/use-request-handle";
import { useAuth } from "@/context/auth/auth-context-utils";

const NotificationsPage: FC = (): ReactElement => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const roleFromStorage = localStorage.getItem("role");
  const role = user?.role || roleFromStorage || "";
  const {
    data: notificationsData,
    isLoading: isLoadingNotifications,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useDoctorNotifications(10, role);
  const { data: countData } = useUnreadNotificationCount(role);

  const notifications =
    notificationsData?.pages.flatMap((page) => page.notifications) ?? [];
  const unreadCount = countData?.unread_count ?? 0;

  const [selectedNotification, setSelectedNotification] =
    useState<NotificationItem | null>(null);
  const [dialogMode, setDialogMode] = useState<"approve" | "decline">(
    "approve",
  );

  const acceptMutation = useAcceptRequest();
  const rejectMutation = useRejectRequest();

  const markAsRead = useMarkNotificationAsRead();

  const markAllAsRead = useMarkAllNotificationsAsRead();
  console.log(markAsRead, markAllAsRead);

  return (
    <div className="h-[calc(100vh-60px)] overflow-auto bg-[#F4F6F9] flex flex-col">
      <div className="p-5 border-b border-gray-200 flex flex-row">
        <h1 className="text-xl font-semibold">
          Notifications
          {unreadCount > 0 && (
            <span className="text-red-500 ml-2">({unreadCount})</span>
          )}
        </h1>

        {notifications.length > 0 && (
          <div className="relative group bg-white mx-auto rounded-full">
            <button
              type="button"
              onClick={() => markAllAsRead.mutate(role)}
              disabled={markAllAsRead.isPending || unreadCount === 0}
              className={`
         p-2 rounded-sm mx-auto transition-all duration-200
        ${
          markAllAsRead.isPending || unreadCount === 0
            ? "opacity-50 cursor-not-allowed text-gray-600 bg-transparent"
            : "text-gray-600 hover:text-blue-600 hover:bg-blue-50 active:bg-blue-100"
        }
      `}
              aria-label="Mark all notifications as read"
            >
              {/* Phosphor icon – CheckCircle ya CheckSquare jo suit kare */}
              <CheckIcon size={20} weight={"bold"} />

              {/* Loading spinner agar pending hai */}
              {markAllAsRead.isPending && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                </div>
              )}
            </button>

            {/* Tooltip on hover */}
            <div
              className="
      absolute top-full right-0 mt-2 px-3 py-1.5 bg-gray-800 text-white text-xs rounded-md
      opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap
      z-10 shadow-md
    "
            >
              Mark all as read
            </div>
          </div>
        )}
      </div>

      <ScrollArea className="flex-1">
        <div className="p-5 pb-10">
          {isLoadingNotifications && notifications.length === 0 && (
            <div className="flex justify-center items-center py-12 text-gray-500">
              Loading notifications...
            </div>
          )}

          {!isLoadingNotifications && notifications.length === 0 && (
            <div className="text-center py-16 text-gray-500">
              <Text size="md" c="dimmed">
                No notifications yet
              </Text>
            </div>
          )}

          {notifications.length > 0 && (
            <div className="space-y-4 mx-auto">
              {notifications.map((notif) => {
                const isPendingRequest =
                  notif.appointment_request &&
                  (notif.type === "REQUEST_RECEIVED" ||
                    notif.status === "PENDING");
                const shouldNavigate = notif.type
                  .toUpperCase()
                  .includes("REQUEST");

                return (
                  <div
                    key={notif.id}
                    className={`p-4 rounded-lg border border-gray-200 hover:border-gray-300 transition-shadow ${notif.is_read ? "bg-white" : "bg-gray-200"} ${
                      shouldNavigate ? "cursor-pointer hover:shadow-sm" : ""
                    }`}
                    onClick={() => {
                      if (!notif.is_read && notif.id) {
                        markAsRead.mutate({ id: notif.id, role });
                      }

                      if (shouldNavigate) {
                        const target =
                          role === "patient"
                            ? "/app/appointments"
                            : "/app/requests";
                        navigate({ to: target });
                      }
                    }}
                  >
                    <p className="font-medium text-base mb-1">{notif.title}</p>
                    <p className="text-sm text-gray-700 mt-2">
                      {notif.message}
                    </p>

                    {notif.appointment_request && (
                      <div className="mt-2 text-sm text-gray-600 flex flex-col md:flex-row justify-between">
                        <div>
                          {notif.appointment_request.patient
                            ? `Patient : ${notif.appointment_request.patient.name}`
                            : `Doctor : ${notif.appointment_request.doctor!.name}`}
                        </div>
                        <div>
                          Service: {notif.appointment_request.service.name}
                        </div>
                      </div>
                    )}

                    <div className="mt-3 text-xs text-gray-500">
                      Scheduled Time :{" "}
                      {new Date(notif.created_at).toLocaleDateString("en-IN", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>

                    {isPendingRequest && notif.appointment_request && (
                      <div className="flex gap-3 justify-end mt-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedNotification(notif);
                            setDialogMode("approve");
                          }}
                          className="flex items-center gap-2 px-4 py-2 bg-[#002FD4] text-white rounded-md hover:opacity-90 text-sm font-medium"
                        >
                          <CheckIcon size={16} weight="bold" />
                          Approve
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedNotification(notif);
                            setDialogMode("decline");
                          }}
                          className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-red-600 rounded-md hover:bg-red-50 text-sm font-medium"
                        >
                          <XCircleIcon size={16} weight="bold" />
                          Decline
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}

              {hasNextPage && (
                <div className="flex justify-center mt-8">
                  <Button
                    onClick={() => fetchNextPage()}
                    loading={isFetchingNextPage}
                    variant="outline"
                    color="blue"
                    size="sm"
                    disabled={isFetchingNextPage}
                  >
                    {isFetchingNextPage ? "Loading more..." : "Load more"}
                  </Button>
                </div>
              )}

              {!hasNextPage && notifications.length > 0 && (
                <div className="text-center mt-8 text-gray-500 text-sm">
                  All notifications loaded
                </div>
              )}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Request Dialog – same as in header */}
      {selectedNotification && selectedNotification.appointment_request && (
        <RequestDialog
          open={true}
          requestId={selectedNotification.appointment_request.id}
          patientName={
            selectedNotification.appointment_request.patient?.name ??
            selectedNotification.appointment_request.doctor?.name ??
            ""
          }
          reason={selectedNotification.appointment_request.service.name}
          requestedTime={`${selectedNotification.appointment_request.preferred_date}T${selectedNotification.appointment_request.preferred_time}`}
          submittedAt={selectedNotification.created_at}
          mode={dialogMode}
          onClose={() => setSelectedNotification(null)}
          onApprove={(waiverPercent) => {
            acceptMutation.mutate(
              { requestId: selectedNotification.appointment_request!.id, waiverPercent },
              {
                onSuccess: () => {
                  toast.success("Request Approved!");
                  setSelectedNotification(null);
                },
                onError: () => toast.error("Failed to approve request"),
              },
            );
          }}
          onDecline={(reason) => {
            rejectMutation.mutate(
              {
                requestId: selectedNotification.appointment_request!.id,
                payload: { rejection_reason: reason },
              },
              {
                onSuccess: () => {
                  toast.success("Request Declined!");
                  setSelectedNotification(null);
                },
                onError: () => toast.error("Failed to decline request"),
              },
            );
          }}
        />
      )}
    </div>
  );
};

export default NotificationsPage;
