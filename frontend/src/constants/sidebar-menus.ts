import {
  ArticleIcon,
  CalendarIcon,
  ChartLineIcon,
  ChatsCircleIcon,
  CreditCardIcon,
  CurrencyDollarSimpleIcon,
  GearIcon,
  HeartbeatIcon,
  HouseIcon,
  IdentificationCardIcon,
  MapPinIcon,
  PercentIcon,
  PrescriptionIcon,
  PresentationIcon,
  ShieldIcon,
  StethoscopeIcon,
  UserPlusIcon,
  UsersIcon,
} from "@phosphor-icons/react";

export const adminSidebarMenuItems = [
  {
    title: "Dashboard",
    url: "/app/dashboard",
    icon: HouseIcon,
  },
  {
    title: "Users",
    url: "/app/users",
    icon: UsersIcon,
  },
  {
    title: "Services",
    url: "/app/services",
    icon: StethoscopeIcon,
  },
  {
    title: "Locations",
    url: "/app/locations",
    icon: MapPinIcon,
  },
  {
    title: "Commissions",
    url: "/app/commissions",
    icon: PercentIcon,
  },
  {
    title: "Webinars",
    url: "/app/webinars",
    icon: PresentationIcon,
  },
  {
    title: "Permissions",
    url: "/app/permissions",
    icon: ShieldIcon,
  },
  {
    title: "Analytics",
    url: "/app/analytics",
    icon: ChartLineIcon,
  },
  {
    title: "Settings",
    url: "/app/settings",
    icon: GearIcon,
  },
];

export const doctorSidebarMenuItems = [
  {
    title: "Appointments",
    url: "/app/appointments",
    icon: HouseIcon,
  },
  {
    title: "Patients",
    url: "/app/patients",
    icon: IdentificationCardIcon,
  },
  {
    title: "Payments",
    url: "/app/payments",
    icon: CurrencyDollarSimpleIcon,
  },
  {
    title: "Requests",
    url: "/app/requests",
    icon: ArticleIcon,
  },
  {
    title: "Webinars",
    url: "/app/webinars",
    icon: PresentationIcon,
  },
  {
    title: "Messages",
    url: "/app/messages",
    icon: ChatsCircleIcon,
  },
  {
    title: "Analytics",
    url: "/app/analytics",
    icon: ChartLineIcon,
  },
  {
    title: "Rx Templates",
    url: "/app/rx-template",
    icon: PrescriptionIcon,
  },
];

export const patientSidebarMenuItems = [
  {
    title: "Dashboard",
    url: "/app/dashboard",
    icon: HouseIcon,
  },
  {
    title: "Healthcare Providers",
    url: "/app/doctors",
    icon: UserPlusIcon,
  },
  {
    title: "Messages",
    url: "/app/messages",
    icon: ChatsCircleIcon,
  },
  {
    title: "Appointments",
    url: "/app/appointments",
    icon: CalendarIcon,
  },
  {
    title: "Documents",
    url: "/app/documents",
    icon: ArticleIcon,
  },
  {
    title: "Webinars",
    url: "/app/webinars",
    icon: PresentationIcon,
  },
  {
    title: "Vital Signs",
    url: "/app/vital-signs",
    icon: HeartbeatIcon,
  },
];

export const staffSidebarMenuItems = [
  {
    title: "Dashboard",
    url: "/app/dashboard",
    icon: HouseIcon,
  },
  {
    title: "Patient Data",
    url: "/app/patient-data",
    icon: UsersIcon,
  },
  {
    title: "Billing",
    url: "/app/billing",
    icon: CreditCardIcon,
  },
];

export const sidebarMenuItemsRecordMapping: Record<string, string> = {
  "/app/dashboard": "Dashboard",
  "/app/users": "Users",
  "/app/services": "Services",
  "/app/locations": "Locations",
  "/app/commissions": "Commissions",
  "/app/webinars": "Webinars",
  "/app/permissions": "Permissions",
  "/app/analytics": "Analytics",
  "/app/settings": "Settings",
  "/app/appointments": "Appointments",
  "/app/patients": "Patients",
  "/app/payments": "Payments",
  "/app/requests": "Requests",
  "/app/messages": "Messages",
  "/app/rx-template": "Rx Templates",
  "/app/doctors": "Healthcare Providers",
  "/app/documents": "Documents",
  "/app/vital-signs": "Vital Signs",
};
