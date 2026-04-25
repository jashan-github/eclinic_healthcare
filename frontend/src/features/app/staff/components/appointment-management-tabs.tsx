// components/ui/custom-dashboard-tabs.tsx

import React from 'react'

type Tab = 'Today' | 'Upcoming'

interface DashboardTabsProps {
    activeTab: Tab
    onTabChange: (tab: Tab) => void
    todayLength: number
    UpcomingLength: number
}

const AppointmentManagementTabs: React.FC<DashboardTabsProps> = ({ activeTab, onTabChange, todayLength, UpcomingLength }) => {
    const tabs = [
        { id: 'Today', label: `Today(${todayLength})` },
        { id: 'Upcoming', label: `Upcoming(${UpcomingLength})` },
    ]

    return (
        <div className="w-full mx-auto">
            <div className="flex bg-white rounded-md">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id as Tab)}
                        className={`
                            flex-1 px-6 py-1 rounded-md hover:cursor-pointer
                            ${activeTab === tab.id
                                ? 'bg-[#002FD4] text-white'
                                : 'text-[#64748B] bg-[#F1F5F9]'
                            }
                        `}
                    >
                        <span className=' font-poppins font-semibold text-sm leading-5 tracking-normal text-center align-middle'>
                            {tab.label}
                        </span>
                    </button>
                ))}
            </div>
        </div>
    )
}

export default AppointmentManagementTabs
