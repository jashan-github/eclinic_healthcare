// components/ui/custom-dashboard-tabs.tsx

import React from "react";

type Tab = "General Settings" | "Notifications Settings" | "Waiver Settings";

interface DashboardTabsProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const AdminSettingsDashboardTabs: React.FC<DashboardTabsProps> = ({
  activeTab,
  onTabChange,
}) => {
  const tabs = [
    { id: "General Settings", label: "General Settings" },
    { id: "Notifications Settings", label: "Notifications Settings" },
    { id: "Waiver Settings", label: "Waiver Settings" },
  ];

  return (
    <div className="w-full mx-auto">
      <div className="flex bg-white rounded-lg border border-[#D1D1D1]">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id as Tab)}
            className={`
                            flex-1 px-6 py-2 rounded-md hover:cursor-pointer
                            ${
                              activeTab === tab.id
                                ? "bg-[#002FD4] text-white"
                                : "text-[#64748B]"
                            }
                        `}
          >
            <span className=" font-poppins font-semibold text-sm leading-5 tracking-normal text-center align-middle">
              {tab.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AdminSettingsDashboardTabs;
