import {
  adminSidebarMenuItems,
  doctorSidebarMenuItems,
  patientSidebarMenuItems,
  staffSidebarMenuItems,
} from "@/constants/sidebar-menus";
import { useAuth } from "@/context/auth/auth-context-utils";
import { getFirstAllowedRoute } from "@/utils/permission-utils";
// import type { UserRoleType } from '@/utils/user-role'
import { Link, useLocation } from "@tanstack/react-router";
import { useEffect, useState, type FC, type ReactElement } from "react";

const AppSidebar: FC = (): ReactElement => {
  const { user, permissions } = useAuth();

  const [showSidebar, setShowSidebar] = useState<boolean>(false);
  // Get role from user object or localStorage as fallback, normalize to proper case
  const roleFromStorage = localStorage.getItem("role");
  const roleRaw = user?.role || roleFromStorage || "doctor";

  // Handle super_admin and admin specially (keep as-is, don't capitalize)
  // const normalizedRole = roleRaw.toLowerCase()
  // const isAdmin = normalizedRole === 'super_admin' || normalizedRole === 'admin'

  // Normalize role to match expected format
  // const role = isAdmin
  //   ? (normalizedRole as UserRoleType)
  //   : (roleRaw.charAt(0).toUpperCase() + roleRaw.slice(1).toLowerCase()) as UserRoleType

  const STAFF_MENU_PERMISSION_MAP: Record<string, string | null> = {
    dashboard: null, // always visible
    patient_data: "patients",
    billing: "payments",
  };

  const normalizedPermissions = new Set(
    permissions?.map((p) => p.toLowerCase()) ?? [],
  );

  const normalizeMenuTitle = (title: string) =>
    title.trim().toLowerCase().replace(/\s+/g, "_");

  const doctorMenu = doctorSidebarMenuItems.filter((menu) =>
    normalizedPermissions.has(normalizeMenuTitle(menu.title)),
  );

  const staffMenu = staffSidebarMenuItems.filter((menu) => {
    const key = normalizeMenuTitle(menu.title);
    const requiredPermission = STAFF_MENU_PERMISSION_MAP[key];

    // no permission required → always show
    if (!requiredPermission) return true;

    return normalizedPermissions.has(requiredPermission);
  });

  const menuItemsByRole = {
    doctor: doctorMenu,
    staff: staffMenu,
    admin: adminSidebarMenuItems,
    super_admin: adminSidebarMenuItems,
    patient: patientSidebarMenuItems,
  };

  const menuItems =
    menuItemsByRole[roleRaw as keyof typeof menuItemsByRole] ??
    doctorSidebarMenuItems;

  // const menuItems = staffSidebarMenuItems;
  const homeUrl = getFirstAllowedRoute(roleRaw, permissions || []);
  const location = useLocation();
  useEffect(() => {
    const isCreateProfile = location.pathname.startsWith("/app/create-profile");
    if (isCreateProfile) {
      setShowSidebar(false);
    } else {
      setShowSidebar(true);
    }
  }, [location]);

  if (!showSidebar) {
    return <></>;
  }

  return (
    <div className="w-[100px] border-gray-200  h-screen z-0 border flex flex-col items-center">
      <div className="h-[60px] w-full hover:bg-[#F4F6F9] flex items-center justify-center">
        <Link
          key="home-link"
          to={homeUrl}
          className="sidebar-nav-link-wrapper h-[60px] flex items-center justify-center text-xs"
        >
          <img
            width={32}
            src="/assets/icons/e-clinic-logo.svg"
            alt="E-Clinic"
          />
        </Link>
      </div>
      <div className="h-[500px] w-full">
        {menuItems?.map((item) => (
          <Link
            key={item.url}
            to={item.url}
            className="sidebar-nav-link-wrapper text-xs"
          >
            <item.icon size={24} weight={"bold"} />
            <span className=" text-xs font-semibold leading-3 text-center align-middle">
              {item.title}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default AppSidebar;
