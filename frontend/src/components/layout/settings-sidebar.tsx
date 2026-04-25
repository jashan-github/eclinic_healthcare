import {
  CaretRightIcon,
  CheckIcon,
  GearSix,
  Heartbeat,
  LockSimpleIcon,
  MegaphoneSimple,
  Pulse,
  StethoscopeIcon,
  Ticket,
} from "@phosphor-icons/react";
import { Link, useLocation } from "@tanstack/react-router";
import { type FC, type ReactElement, useMemo, useState } from "react";
import { useAuth } from "@/context/auth/auth-context-utils";

type Tab = {
  id: string;
  label: string;
  icon: React.ReactNode;
  url: string;
};

const SettingsSidebar: FC = (): ReactElement => {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const settingsSidebarTab: Tab[] = useMemo(() => {
    const roleFromStorage = localStorage.getItem("role");
    const role = (user?.role || roleFromStorage || "doctor").toLowerCase();
    const isAdmin =
      role === "admin" || role === "super_admin" || role === "clinic_admin";

    if (isAdmin) {
      return [
        {
          id: "general-settings",
          label: "General Settings",
          icon: <GearSix size={24} weight="fill" />,
          url: "/app/settings/general-settings",
        },
        {
          id: "notifications-settings",
          label: "Notifications Settings",
          icon: <MegaphoneSimple size={24} weight="fill" />,
          url: "/app/settings/notifications-settings",
        },
        {
          id: "waiver-referral-settings",
          label: "Waiver Settings",
          icon: <Ticket size={24} weight="fill" />,
          url: "/app/settings/waiver-referral-settings",
        },
        {
          id: "vitals-settings",
          label: "Vitals Settings",
          icon: <Heartbeat size={24} weight="fill" />,
          url: "/app/settings/vitals-settings",
        },
        {
          id: "speciality-settings",
          label: "Speciality Settings",
          icon: <Pulse size={24} weight="fill" />,
          url: "/app/settings/speciality-settings",
        },
      ];
    }

    return [
      {
        id: "staff-restrictions",
        label: "Staff Restrictions",
        icon: <LockSimpleIcon size={24} weight="fill" />,
        url: "/app/settings/staff-restrictions",
      },
      {
        id: "fees-settings",
        label: "Fees Settings",
        icon: <StethoscopeIcon size={24} weight="fill" />,
        url: "/app/settings/fees-settings",
      },
      // ,{
      //   id: 'vitals-settings',
      //   label: 'Vitals Settings',
      //   icon: <Heartbeat size={24} weight="fill" />,
      //   url: '/app/settings/vitals-settings'
      // }
    ];
  }, [user?.role]);

  return (
    <div
      className={`relative h-full bg-white transition-all duration-200 ${collapsed ? "w-[68px]" : "w-[300px]"}`}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        {!collapsed && (
          <span className="font-poppins text-sm font-semibold text-[#0F1011]">
            Settings
          </span>
        )}
        <button
          type="button"
          onClick={() => setCollapsed((v) => !v)}
          className="p-1 rounded-md hover:bg-[#002FD4]/90 text-white absolute -right-2 top-[50%] bg-[#002FD4] hover:cursor-pointer"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <CaretRightIcon size={18} weight="bold" />
          ) : (
            <CaretRightIcon size={18} weight="bold" className="rotate-180" />
          )}
        </button>
      </div>
      {settingsSidebarTab.map(({ id, label, icon, url }) => {
        const isActive = pathname === url;

        return (
          <Link
            key={id}
            to={url}
            className={`flex justify-between items-center px-4 py-3 transition-all border-t border-t-gray-100 last:border-b last:border-b-gray-100 ${
              isActive
                ? "bg-[#F4F6F9] text-[#002FD4] font-bold border-t-0 border-r border-b border-l-0 border-[#EDEFF2]"
                : "bg-white text-[#0F1011] font-normal hover:text-primary/80"
            }`}
          >
            <div className="flex gap-3 items-center">
              <div>{icon}</div>
              {!collapsed && (
                <span className="font-poppins text-sm leading-5">{label}</span>
              )}
            </div>

            <div>
              {isActive ? (
                <CheckIcon size={18} weight="bold" />
              ) : (
                <CaretRightIcon
                  size={16}
                  weight="bold"
                  className={collapsed ? "" : ""}
                />
              )}
            </div>
          </Link>
        );
      })}
    </div>
  );
};

export default SettingsSidebar;
