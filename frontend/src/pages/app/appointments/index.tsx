import { useViewStore } from "@/context/view-context/view-context";
import ManageOngoingAppointments from "@/features/app/appointments/components";
import PatientAppointments from "@/components/e-clinic/patient/appointments/patient-appointments";
import CalendarView from "@/features/app/appointments/components/calendar-view";
import { useAuth } from "@/context/auth/auth-context-utils";
import { useEffect, type FC, type ReactElement } from "react";
import { useNavigate } from "@tanstack/react-router";
import type { UserRoleType } from "@/utils/user-role";

const AppointmentsPage: FC = (): ReactElement => {
  const view = useViewStore((s) => s.view);
  const { user } = useAuth();
  const navigate = useNavigate();

  // Get role from user or localStorage
  const roleFromStorage = localStorage.getItem("role");
  const userRole = (user?.role || roleFromStorage || "doctor") as UserRoleType;
  const isPatient = userRole === "patient";

  useEffect(() => {
    if (!user) return;
    if (userRole === "doctor" && !user.is_profile_complete) {
      navigate({ to: "/app/create-profile" });
    }
  }, [navigate, user, userRole]);

  // For patients, show patient appointments UI
  if (isPatient) {
    return <PatientAppointments />;
  }

  // For doctors/admin/staff, show existing appointments UI
  return (
    <div className="h-screen overflow-auto">
      {view === "calendar" ? (
        <CalendarView />
      ) : (
        <div className="flex bg-white flex-row gap-4 p-4 h-full overflow-y-scroll">
          <div className="w-12/12">
            <ManageOngoingAppointments />
          </div>
        </div>
      )}
    </div>
  );
};

export default AppointmentsPage;
