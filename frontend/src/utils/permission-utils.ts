import {
  doctorSidebarMenuItems,
  staffSidebarMenuItems,
} from "@/constants/sidebar-menus";

const STAFF_MENU_PERMISSION_MAP: Record<string, string | null> = {
  dashboard: null,
  patient_data: "patients",
  billing: "payments",
};

const normalizeMenuTitle = (title: string) =>
  title.trim().toLowerCase().replace(/\s+/g, "_");

/**
 * Get the first allowed route based on user role and permissions.
 * This is used after login to redirect the user to an accessible page.
 */
export function getFirstAllowedRoute(
  role: string,
  permissions: string[] = [],
): string {
  const normalizedRole = role.toLowerCase();
  const normalizedPermissions = new Set(
    permissions.map((p) => p.toLowerCase()),
  );

  // Admin roles always go to dashboard
  if (
    normalizedRole === "admin" ||
    normalizedRole === "super_admin" ||
    normalizedRole === "clinic_admin"
  ) {
    return "/app/dashboard";
  }

  // Patient role goes to dashboard
  if (normalizedRole === "patient") {
    return "/app/dashboard";
  }

  // Doctor role - find first allowed menu item
  if (normalizedRole === "doctor") {
    const allowedMenu = doctorSidebarMenuItems.find((menu) =>
      normalizedPermissions.has(normalizeMenuTitle(menu.title)),
    );
    // Return the first allowed route, or dashboard as fallback
    return allowedMenu?.url ?? "/app/appointments";
  }

  // Staff role - find first allowed menu item
  if (normalizedRole === "staff") {
    const allowedMenu = staffSidebarMenuItems.find((menu) => {
      const key = normalizeMenuTitle(menu.title);
      const requiredPermission = STAFF_MENU_PERMISSION_MAP[key];

      // No permission required → always allowed
      if (!requiredPermission) return true;

      return normalizedPermissions.has(requiredPermission);
    });
    return allowedMenu?.url ?? "/app/dashboard";
  }

  // Default fallback
  return "/app/dashboard";
}

/**
 * Check if a user has permission to access a specific route.
 */
export function hasRoutePermission(
  role: string,
  permissions: string[],
  route: string,
): boolean {
  const normalizedRole = role.toLowerCase();
  const normalizedPermissions = new Set(
    permissions.map((p) => p.toLowerCase()),
  );

  // Admin roles have access to all routes
  if (
    normalizedRole === "admin" ||
    normalizedRole === "super_admin" ||
    normalizedRole === "clinic_admin"
  ) {
    return true;
  }

  // Doctor role - check if route is in allowed menu
  if (normalizedRole === "doctor") {
    const menuItem = doctorSidebarMenuItems.find((menu) => menu.url === route);
    if (!menuItem) return true; // Route not in doctor menu, allow access
    return normalizedPermissions.has(normalizeMenuTitle(menuItem.title));
  }

  // Staff role - check permission map
  if (normalizedRole === "staff") {
    const menuItem = staffSidebarMenuItems.find((menu) => menu.url === route);
    if (!menuItem) return true; // Route not in staff menu, allow access
    const key = normalizeMenuTitle(menuItem.title);
    const requiredPermission = STAFF_MENU_PERMISSION_MAP[key];
    if (!requiredPermission) return true; // No permission required
    return normalizedPermissions.has(requiredPermission);
  }

  return true;
}
