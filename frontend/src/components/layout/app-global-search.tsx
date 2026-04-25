import { Button } from "@mantine/core";
import {
  Spotlight,
  spotlight,
  type SpotlightActionData,
} from "@mantine/spotlight";
import { MagnifyingGlassIcon } from "@phosphor-icons/react";
import { type FC, type ReactElement } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useAuth } from "@/context/auth/auth-context-utils";

type AppGlobalSearchProps = {
  placeholder?: string;
};

const AppGlobalSearch: FC<AppGlobalSearchProps> = ({
  placeholder = "Search anything...",
}): ReactElement => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const roleFromStorage = localStorage.getItem("role");
  const role = (user?.role || roleFromStorage || "").toLowerCase().trim();

  const getActions = (): SpotlightActionData[] => {
    const commonSearchIcon = <MagnifyingGlassIcon size={24} />;

    if (role === "doctor") {
      return [
        {
          id: "appointments",
          label: "Appointments",
          description: "View and manage patient appointments & schedule",
          onClick: () => navigate({ to: "/app/appointments" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "rx-template",
          label: "Rx Templates",
          description: "Create and manage prescription templates",
          onClick: () => navigate({ to: "/app/rx-template" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "analytics",
          label: "Analytics",
          description: "View practice performance and insights",
          onClick: () => navigate({ to: "/app/analytics" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "messages",
          label: "Messages",
          description: "Communicate with patients",
          onClick: () => navigate({ to: "/app/messages" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "webinars",
          label: "Webinars",
          description: "Access webinars",
          onClick: () => navigate({ to: "/app/webinars" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "payments",
          label: "Payments",
          description: "Manage payments",
          onClick: () => navigate({ to: "/app/payments" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "patients",
          label: "Patients",
          description: "Access patient records and history",
          onClick: () => navigate({ to: "/app/patients" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "requests",
          label: "Requests",
          description: "View & handle patient requests",
          onClick: () => navigate({ to: "/app/requests" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "calendar",
          label: "Calendar",
          description: "View full schedule and availability",
          onClick: () => navigate({ to: "/app/calendar" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "my-profile",
          label: "My Profile",
          description: "Update personal and professional details",
          onClick: () => navigate({ to: "/app/my-profile" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "settings",
          label: "Settings",
          description: "Configure account",
          onClick: () => navigate({ to: "/app/settings" }),
          leftSection: commonSearchIcon,
        },
      ];
    }

    if (role === "patient") {
      return [
        {
          id: "dashboard",
          label: "Dashboard",
          description: "Overview of your profile",
          onClick: () => navigate({ to: "/app/dashboard" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "doctors",
          label: "Find Doctors",
          description: "Search and book doctors",
          onClick: () => navigate({ to: "/app/doctors" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "appointments",
          label: "My Appointments",
          description: "View upcoming and past appointments",
          onClick: () => navigate({ to: "/app/appointments" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "documents",
          label: "Documents",
          description: "View and upload documents",
          onClick: () => navigate({ to: "/app/documents" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "messages",
          label: "Messages",
          description: "Chat with your doctor",
          onClick: () => navigate({ to: "/app/messages" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "webinars",
          label: "Webinars",
          description: "Join health awareness webinars",
          onClick: () => navigate({ to: "/app/webinars" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "vital-signs",
          label: "Vital Signs",
          description: "Track and monitor your health vitals",
          onClick: () => navigate({ to: "/app/vital-signs" }),
          leftSection: commonSearchIcon,
        },
      ];
    }

    if (role === "staff") {
      return [
        {
          id: "dashboard",
          label: "Dashboard",
          description: "Your profile overview",
          onClick: () => navigate({ to: "/app/dashboard" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "patients-data",
          label: "Patients Data",
          description: "View patient details",
          onClick: () => navigate({ to: "/app/patient-data" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "billing",
          label: "Billing",
          description: "View patient billing and invoices",
          onClick: () => navigate({ to: "/app/billing" }),
          leftSection: commonSearchIcon,
        },
      ];
    }

    if (role === "admin" || role === "clinic_admin" || role === "super_admin") {
      return [
        {
          id: "dashboard",
          label: "Dashboard",
          description: "System-wide overview and stats",
          onClick: () => navigate({ to: "/app/dashboard" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "users",
          label: "Users",
          description: "Manage doctors, staff, patients & accounts",
          onClick: () => navigate({ to: "/app/users" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "webinars",
          label: "Webinars",
          description: "Create and manage webinars",
          onClick: () => navigate({ to: "/app/webinars" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "services",
          label: "Services",
          description: "Configure available medical services",
          onClick: () => navigate({ to: "/app/services" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "locations",
          label: "Locations",
          description: "Manage clinic branches and addresses",
          onClick: () => navigate({ to: "/app/locations" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "commissions",
          label: "Commissions",
          description: "Track and manage doctor/staff commissions",
          onClick: () => navigate({ to: "/app/commissions" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "analytics",
          label: "Analytics",
          description: "Detailed reports and business insights",
          onClick: () => navigate({ to: "/app/analytics" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "permissions",
          label: "Permissions",
          description: "Control user roles and access rights",
          onClick: () => navigate({ to: "/app/permissions" }),
          leftSection: commonSearchIcon,
        },
        {
          id: "settings",
          label: "Settings",
          description: "Global system configuration & preferences",
          onClick: () => navigate({ to: "/app/settings" }),
          leftSection: commonSearchIcon,
        },
      ];
    }

    // Fallback for unknown / no role
    return [
      {
        id: "home",
        label: "Home",
        description: "Go to main dashboard",
        onClick: () => navigate({ to: "/app/dashboard" }),
        leftSection: commonSearchIcon,
      },
    ];
  };

  const actions = getActions();

  return (
    <>
      <Button
        justify="flex-start"
        color="gray.5"
        variant="outline"
        onClick={spotlight.open}
        className="border-[#d1d1d1]"
        leftSection={<MagnifyingGlassIcon />}
        w={250}
      >
        Search
      </Button>

      <Spotlight
        actions={actions}
        nothingFound="Nothing found..."
        highlightQuery
        searchProps={{
          leftSection: <MagnifyingGlassIcon size={20} />,
          placeholder: placeholder || `Search as ${role || "user"}...`,
        }}
      />
    </>
  );
};

export default AppGlobalSearch;
