import AppHeader from "@/components/layout/app-header";
import AppSidebar from "@/components/layout/app-sidebar";
import { useHeaderStore } from "@/store/use-header-store";
import { Outlet, useLocation } from "@tanstack/react-router";
import { useEffect, type FC, type ReactElement } from "react";

const AppLayout: FC = (): ReactElement => {
  const { showHeader, setShowHeader } = useHeaderStore();
  const location = useLocation();

  // Check if this is a payment page opened in popup
  const isPaymentPage = location.pathname.startsWith("/app/payment/");
  const isPopup = typeof window !== "undefined" && window.opener !== null;

  useEffect(() => {
    const isPatientRoute =
      location.pathname.startsWith("/app/patients/") &&
      location.pathname.split("/").length > 3;
    const isCreateProfile = location.pathname.startsWith("/app/create-profile");
    if (isPatientRoute) {
      setShowHeader(false);
    } else if (isCreateProfile) {
      setShowHeader(false);
    } else {
      setShowHeader(true);
    }
  }, [location, setShowHeader]);

  // If payment page in popup, render without layout (no header/sidebar)
  if (isPaymentPage && isPopup) {
    return <Outlet />;
  }

  return (
    <div className="h-screen w-screen flex gap-0">
      <AppSidebar />
      <div className="flex flex-col h-screen overflow-hidden w-full">
        {showHeader && <AppHeader />}
        <Outlet />
      </div>
    </div>
  );
};

export default AppLayout;
