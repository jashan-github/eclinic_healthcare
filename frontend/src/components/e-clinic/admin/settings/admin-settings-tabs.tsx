// app/dashboard/page.tsx ya kahi bhi
import { useState } from "react";
import AdminSettingsDashboardTabs from "./admin-settings-dashboard-tabs";
import GeneralSettings from "./general-settings";
import AppointmentSettings from "./appointment-settings";

export default function AdminSettingsTabs() {
  const [activeTab, setActiveTab] = useState<
    "General Settings" | "Notifications Settings" | "Waiver Settings"
  >("General Settings");

  return (
    <div>
      {/* Tabs */}
      <div className="mb-8">
        <AdminSettingsDashboardTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      </div>

      {/* Content Area */}
      <div className="p-2">
        {/* Chart Area */}
        <div>
          {activeTab === "General Settings" && (
            <>
              <GeneralSettings />
              <AppointmentSettings />
            </>
          )}
          {activeTab === "Notifications Settings" && (
            <div className="text-center">
              <p className="text-gray-500 font-poppins">
                Appointment Chart Here
              </p>
            </div>
          )}
          {activeTab === "Waiver Settings" && (
            <div className="text-center">
              <p className="text-gray-500 font-poppins">Waiver Settings</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
