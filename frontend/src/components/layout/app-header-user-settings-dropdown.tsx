import { useAuth } from "@/context/auth/auth-context-utils";
import InviteCard from "@/features/app/my-profile/components/my-profile/invite-card";
import {
  useAcceptRequest,
  useRejectRequest,
} from "@/features/app/requests/hooks/use-request-handle";
import {
  useDoctorNotifications,
  useMarkAllNotificationsAsRead,
  useMarkNotificationAsRead,
  useUnreadNotificationCount,
} from "@/hooks/use-notifications";
import { usePatientPersonalInfo } from "@/hooks/use-patient-personal-info";
import type { UserRoleType } from "@/utils/user-role";
import {
  Avatar,
  Badge,
  Divider,
  Indicator,
  Menu,
  Popover,
  ScrollArea,
  Text,
} from "@mantine/core";
import {
  ArrowRight,
  CalendarIcon,
  CaretDownIcon,
  CheckIcon,
  // ClipboardIcon,
  GearIcon,
  // LaptopIcon,
  SignOutIcon,
  UserIcon,
  WalletIcon,
  XCircleIcon,
} from "@phosphor-icons/react";
import { Link, useNavigate, useRouter } from "@tanstack/react-router";
import { useMemo, type FC, useState } from "react";
import { toast } from "react-toastify";
import RequestDialog from "@/components/e-clinic/doctor/requests/request-dialog"; // Assuming this path, adjust if needed
import type { NotificationItem } from "@/services/notifications-service"; // Assuming this type import from your service

const AppHeaderUserSettingsDropdown: FC = () => {
  const router = useRouter();
  const navigate = useNavigate();

  const { user, logout } = useAuth();

  // Get role from user or localStorage
  const roleFromStorage = localStorage.getItem("role");
  const userRole = (user?.role || roleFromStorage || "doctor") as UserRoleType;
  const isPatient = userRole === "patient";
  const isAdmin = userRole === "super_admin" || userRole === "clinic_admin";
  const isStaff = userRole === "staff";

  // Map role to display name (user-facing text)
  const getRoleDisplayName = (role: UserRoleType): string => {
    const roleMap: Record<string, string> = {
      doctor: "HEALTHCARE PROVIDER",
      healthcare_provider: "HEALTHCARE PROVIDER",
      patient: "PATIENT",
      staff: "STAFF",
      admin: "ADMIN",
      super_admin: "ADMIN",
      clinic_admin: "ADMIN",
    };
    return roleMap[role] || role.toUpperCase();
  };

  // Fetch patient personal info if user is a Patient
  const { data: patientInfo, isLoading: isLoadingPatientInfo } =
    usePatientPersonalInfo(isPatient);
  const [notificationsOpened, setNotificationsOpened] = useState(false);

  const role = user?.role || roleFromStorage || "";
  const {
    data: notificationsData,
    isLoading: isLoadingNotifications,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useDoctorNotifications(10, role, {
    enabled: notificationsOpened && !isStaff,
  });
  const { data: countData } = useUnreadNotificationCount(role, {
    enabled: role === "doctor" || role === "patient",
  });

  const notifications =
    notificationsData?.pages.flatMap((page) => page.notifications) ?? [];
  const unreadCount = countData?.unread_count ?? 0;

  // Get display name and invite code based on role
  const displayName = useMemo(() => {
    if (isAdmin) {
      return "Admin";
    }
    if (isPatient && patientInfo) {
      return (
        patientInfo.full_name ||
        patientInfo.first_name ||
        `${patientInfo.first_name || ""} ${patientInfo.last_name || ""}`.trim() ||
        user?.name ||
        "Patient"
      );
    }
    if (isStaff) {
      return user?.first_name || user?.name || "Staff";
    }
    return user?.first_name || user?.name || "User";
  }, [isPatient, patientInfo, user, isStaff]);

  const inviteCode = useMemo(() => {
    if (isPatient && patientInfo?.invite_code) {
      return patientInfo.invite_code;
    }
    return user?.doctor_code || "";
  }, [isPatient, patientInfo, user]);

  const profileImage = useMemo(() => {
    if (!user || !user.avatar) return;
    return user.avatar;
  }, [user]);

  // Get avatar initial - for staff, use staff user's name, not doctor's name
  const avatarInitial = useMemo(() => {
    if (isStaff) {
      const staffName = user?.first_name || user?.name || "S";
      return staffName.charAt(0).toUpperCase();
    }
    return displayName?.[0]?.toUpperCase() || "U";
  }, [isStaff, user, displayName]);

  const processLogout = (): void => {
    logout();
    router.invalidate().then(() => {
      navigate({ to: "/auth/login" });
    });
  };

  const acceptMutation = useAcceptRequest();
  const rejectMutation = useRejectRequest();

  const markAsRead = useMarkNotificationAsRead();
  const markAllAsRead = useMarkAllNotificationsAsRead();

  const [selectedNotification, setSelectedNotification] =
    useState<NotificationItem | null>(null);
  const [dialogMode, setDialogMode] = useState<"approve" | "decline">(
    "approve",
  );

  return (
    <div className="flex items-center gap-3">
      {/* Notifications Popover Panel - Hidden for staff */}
      {!isStaff && !isAdmin && (
        <Popover
          width={340}
          position="bottom-end"
          shadow="md"
          offset={10}
          withArrow
          opened={notificationsOpened}
          onChange={setNotificationsOpened}
        >
          <Popover.Target>
            <div
              onClick={() => setNotificationsOpened((o) => !o)}
              className="cursor-pointer"
            >
              <Indicator
                color="#EF4444"
                inline
                label={
                  unreadCount > 0
                    ? unreadCount > 99
                      ? "99+"
                      : unreadCount
                    : null
                }
                offset={6}
                position="top-end"
                size={18}
                withBorder
                disabled={unreadCount === 0}
              >
                <Avatar
                  color="blue"
                  src={profileImage}
                  name={avatarInitial}
                  size="md"
                  radius="xl"
                  className="cursor-pointer ring-2 ring-white hover:ring-gray-300 transition-shadow"
                />
              </Indicator>
            </div>
          </Popover.Target>

          <Popover.Dropdown p={0}>
            <ScrollArea h={400} type="hover">
              <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <p className="font-poppins font-bold text-base text-[#0F1011]">
                    Notifications
                    <span className="text-red-500 ml-2">({unreadCount})</span>
                  </p>

                  <div className="flex items-center gap-4">
                    {notifications.length > 0 && (
                      <div className="relative group">
                        <button
                          type="button"
                          onClick={() => markAllAsRead.mutate(role)}
                          disabled={
                            markAllAsRead.isPending || unreadCount === 0
                          }
                          className={`
                            p-2 rounded-full transition-all duration-200 flex items-center justify-center
                            ${
                              markAllAsRead.isPending || unreadCount === 0
                                ? "opacity-50 cursor-not-allowed text-gray-600"
                                : "text-gray-600 hover:text-blue-600 hover:bg-blue-50 active:bg-blue-100"
                            }
                            `}
                          aria-label="Mark all notifications as read"
                        >
                          <CheckIcon size={20} weight="bold" />

                          {markAllAsRead.isPending && (
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                            </div>
                          )}
                        </button>

                        <div
                          className="
                          absolute top-full right-0 mt-2 px-3 py-1.5 bg-gray-800 text-white text-xs rounded-md
                          opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10 shadow-md
                        "
                        >
                          Mark all as read
                        </div>
                      </div>
                    )}

                    <div className="relative group">
                      <button
                        type="button"
                        onClick={() => {
                          setNotificationsOpened(false);
                          navigate({ to: "/app/notifications" });
                        }}
                        className="
                          p-2 rounded-full text-gray-600 hover:text-blue-600 hover:bg-blue-50 active:bg-blue-100 transition-all duration-200 flex items-center justify-center"
                        aria-label="See all notifications"
                      >
                        <ArrowRight size={20} weight="bold" />
                      </button>

                      <div
                        className="
                        absolute top-full right-0 mt-2 px-3 py-1.5 bg-gray-800 text-white text-xs rounded-md
                        opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10 shadow-md
                        "
                      >
                        See All
                      </div>
                    </div>
                  </div>
                </div>

                {isLoadingNotifications && (
                  <div className="flex justify-center items-center py-8">
                    Loading...
                  </div>
                )}

                {!isLoadingNotifications && notifications.length === 0 && (
                  <Text size="sm" c="dimmed" ta="center" mt="md">
                    No new notifications
                  </Text>
                )}

                {!isLoadingNotifications && notifications.length > 0 && (
                  <div className="space-y-3">
                    {notifications.map((notif) => {
                      const isPendingRequest =
                        notif.appointment_request &&
                        (notif.type === "REQUEST_RECEIVED" ||
                          notif.status === "PENDING");
                      const requestId = notif.appointment_request?.id;
                      const shouldNavigate = notif.type
                        .toUpperCase()
                        .includes("REQUEST");

                      return (
                        <div
                          key={notif.id}
                          className={`p-4 rounded-lg border border-gray-200 hover:border-gray-300 transition-shadow ${notif.is_read ? "bg-white" : "bg-gray-200"} ${shouldNavigate ? "cursor-pointer hover:shadow-sm" : ""}`}
                          onClick={() => {
                            if (!notif.is_read && notif.id) {
                              markAsRead.mutate({ id: notif.id, role });
                            }
                            if (shouldNavigate) {
                              const targetPath =
                                role === "patient"
                                  ? "/app/appointments"
                                  : "/app/requests";
                              navigate({ to: targetPath });
                            }
                          }}
                        >
                          <p className="font-medium text-sm">{notif.title}</p>
                          <p className="text-xs text-gray-600 mt-1">
                            {notif.message}
                          </p>

                          {notif.appointment_request && (
                            <div className="text-xs text-gray-500 mt-2">
                              {notif.appointment_request.patient?.name && (
                                <span>
                                  Patient:{" "}
                                  {notif.appointment_request.patient.name}
                                </span>
                              )}
                              {notif.appointment_request.patient?.name &&
                                notif.appointment_request.service?.name && (
                                  <br />
                                )}
                              {notif.appointment_request.service?.name && (
                                <span>
                                  Service:{" "}
                                  {notif.appointment_request.service.name}
                                </span>
                              )}
                            </div>
                          )}

                          <Text size="xs" c="dimmed" mt={4}>
                            {new Date(notif.created_at).toLocaleDateString(
                              "en-IN",
                              {
                                day: "numeric",
                                month: "short",
                                hour: "2-digit",
                                minute: "2-digit",
                              },
                            )}
                          </Text>

                          {isPendingRequest &&
                            requestId &&
                            user?.role === "doctor" && (
                              <div className="flex gap-3 justify-end mt-3">
                                <button
                                  onClick={(e) => {
                                    if (
                                      selectedNotification &&
                                      !selectedNotification?.is_read
                                    ) {
                                      markAsRead.mutate({
                                        id: selectedNotification.id,
                                        role,
                                      });
                                    }
                                    e.stopPropagation();
                                    setSelectedNotification(notif);
                                    setDialogMode("approve");
                                  }}
                                  className="flex items-center w-[113px] h-8 rounded-md px-3 py-[7.5px] bg-[#002FD4] gap-2 text-white hover:opacity-90"
                                >
                                  <CheckIcon size={18} weight="bold" />
                                  <span className="font-poppins font-semibold text-sm">
                                    Approve
                                  </span>
                                </button>
                                <button
                                  onClick={(e) => {
                                    if (
                                      selectedNotification &&
                                      !selectedNotification?.is_read
                                    ) {
                                      markAsRead.mutate({
                                        id: selectedNotification.id,
                                        role,
                                      });
                                    }
                                    e.stopPropagation();
                                    setSelectedNotification(notif);
                                    setDialogMode("decline");
                                  }}
                                  className="w-[107px] h-8 rounded-md border border-[#E2E8F0] bg-white px-[13px] pt-[7.5px] pb-[8.5px] flex items-center gap-2 text-[#DC2626]"
                                >
                                  <XCircleIcon size={18} weight="bold" />
                                  <span className="font-poppins font-semibold text-sm">
                                    Decline
                                  </span>
                                </button>
                              </div>
                            )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {hasNextPage && (
                  <div className="mt-4 text-center">
                    <button
                      onClick={() => fetchNextPage()}
                      disabled={isFetchingNextPage}
                      className="text-blue-600 text-sm font-medium hover:underline disabled:opacity-50"
                    >
                      {isFetchingNextPage ? "Loading..." : "View more"}
                    </button>
                  </div>
                )}
              </div>
            </ScrollArea>
          </Popover.Dropdown>
        </Popover>
      )}

      {/* Avatar for staff (without notification popover) */}
      {isStaff && (
        <Avatar
          color="blue"
          src={profileImage}
          name={avatarInitial}
          size="md"
          radius="xl"
          className="cursor-pointer ring-2 ring-white hover:ring-gray-300 transition-shadow"
        />
      )}

      {/* User Settings Click Dropdown */}
      <Menu position="bottom-end" width={300} withArrow>
        <Menu.Target>
          <div className="flex items-center gap-2 cursor-pointer select-none">
            <div className="capitalize text-sm font-bold">
              {isStaff
                ? `${displayName}`
                : !isPatient && !isAdmin
                  ? `Dr. ${displayName}`
                  : !isAdmin
                    ? displayName
                    : ""}
            </div>

            <Badge color="primary.5" variant="filled" radius="sm">
              {isAdmin ? "Admin" : getRoleDisplayName(userRole)}
            </Badge>

            <CaretDownIcon size={16} weight="bold" />
          </div>
        </Menu.Target>

        <Menu.Dropdown
          style={{
            width: 280,
            maxHeight: 540,
            padding: 0,
            borderRadius: 8,
            boxShadow: "6px 7px 20px 0px #0000001A",
            overflow: "hidden",
          }}
        >
          {!isLoadingPatientInfo && !isStaff && (
            <InviteCard name={displayName} inviteCode={inviteCode} />
          )}

          <div className="flex flex-col gap-0">
            {!isStaff && !isAdmin && (
              <Menu.Item
                component={Link}
                to={isPatient ? "/app/patient-profile" : "/app/my-profile"}
                leftSection={<UserIcon size={20} />}
                className="font-poppins font-normal text-[13px] leading-[20px] flex items-center h-10"
              >
                My Profile
              </Menu.Item>
            )}

            {!isPatient && !isAdmin && !isStaff && (
              <>
                {/* <Menu.Item
                  component={Link}
                  to="/app/my-patient-referrals"
                  leftSection={<ClipboardIcon size={20} />}
                  className="font-poppins font-normal text-[13px] leading-[20px] flex items-center h-10"
                >
                  My Patient Referrals
                </Menu.Item> */}
                <Menu.Item
                  component={Link}
                  to="/app/calendar"
                  leftSection={<WalletIcon size={20} />}
                  className="font-poppins font-normal text-[13px] leading-[20px] flex items-center h-10"
                >
                  My Availability
                </Menu.Item>
              </>
            )}

            {!isStaff && !isAdmin && (
              <Menu.Item
                component={Link}
                to="/app/notifications"
                leftSection={<CalendarIcon size={20} />}
                className="font-poppins font-normal text-[13px] leading-[20px] flex items-center h-10"
              >
                Notifications
              </Menu.Item>
            )}

            {!isPatient && !isStaff && (
              <>
                <Divider />

                <Menu.Item
                  component={Link}
                  to={
                    isAdmin
                      ? "/app/settings/general-settings"
                      : "/app/settings/staff-restrictions"
                  }
                  leftSection={<GearIcon size={20} />}
                  className="font-poppins font-normal text-[13px] leading-[20px] flex items-center h-10"
                >
                  Settings & Preferences
                </Menu.Item>
              </>
            )}

            {/* {!isPatient && !isAdmin && !isStaff && (
              <>
                <Divider />
                <Menu.Item
                  c="blue.6"
                  styles={{
                    item: {
                      '&:hover': { backgroundColor: '#dbeafe', color: '#2563eb' }
                    }
                  }}
                  leftSection={<LaptopIcon size={20} />}
                  className="font-poppins font-normal text-[13px] leading-[20px] flex items-center h-10"
                >
                  Download patient database
                </Menu.Item>
              </>
            )} */}

            <Divider />

            <Menu.Item
              c="red.6"
              onClick={processLogout}
              styles={{
                item: {
                  "&:hover": { backgroundColor: "#fee2e2", color: "#dc2626" },
                },
              }}
              leftSection={<SignOutIcon size={20} />}
              className="font-poppins font-normal text-[13px] leading-[20px] flex items-center h-10"
            >
              Logout
            </Menu.Item>

            {!isStaff && (
              <>
                <Divider />

                <div className="bg-[#F4F6FA] flex justify-center items-center flex-nowrap gap-1 font-normal text-[11px] leading-4 px-4 py-[10px] rounded-b-lg select-none">
                  <span
                    style={{
                      fontSize: 12,
                      lineHeight: "16px",
                      whiteSpace: "nowrap",
                      color: "#374151",
                      textDecoration: "none",
                    }}
                    onClick={() => navigate({ to: "/privacy-policy" })}
                    className="hover:underline cursor-pointer"
                  >
                    Privacy Policy
                  </span>

                  <span
                    style={{
                      fontSize: 11,
                      lineHeight: "16px",
                      color: "#9CA3AF",
                      margin: "0 8px",
                    }}
                  >
                    •
                  </span>

                  <span
                    style={{
                      fontSize: 12,
                      lineHeight: "16px",
                      whiteSpace: "nowrap",
                      color: "#374151",
                      textDecoration: "none",
                    }}
                    onClick={() => navigate({ to: "/terms-and-conditions" })}
                    className="hover:underline cursor-pointer"
                  >
                    Terms & Conditions
                  </span>
                </div>
              </>
            )}
          </div>
        </Menu.Dropdown>
      </Menu>

      {/* Request Dialog for Approve/Decline */}
      {selectedNotification &&
        selectedNotification.appointment_request &&
        selectedNotification.appointment_request.patient?.name &&
        selectedNotification.appointment_request.service?.name && (
          <RequestDialog
            open={true}
            requestId={selectedNotification.appointment_request.id}
            patientName={selectedNotification.appointment_request.patient.name}
            reason={selectedNotification.appointment_request.service.name}
            requestedTime={`${selectedNotification.appointment_request.preferred_date || ""}T${selectedNotification.appointment_request.preferred_time || ""}`}
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
                  onError: () => {
                    toast.error("Failed to approve request");
                  },
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
                  onError: () => {
                    toast.error("Failed to decline request");
                  },
                },
              );
            }}
          />
        )}
    </div>
  );
};

export default AppHeaderUserSettingsDropdown;
