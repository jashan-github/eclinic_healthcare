// src/pages/calendar/CalendarPage.tsx
import CalendarWeekView from '@/features/app/calendar/components/calendar-week-view'
import CalendarSchedule from '@/features/app/calendar/components/calender-schedule'
import ViewToggle from '@/features/app/calendar/components/view-toggle'
import CalendarServices from '@/features/app/calendar/components/calendar-services'
import CreateNewService from '@/features/app/calendar/components/calendar-services/create-new-service'
import { Card, Tabs } from '@mantine/core'
import { ArrowLeftIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

const CalendarPage: FC = (): ReactElement => {
  const [activeTab, setActiveTab] = useState<string | null>('list')
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="h-screen overflow-hidden bg-[#F4F6F9]">
      <Tabs
        variant="pills"
        className="h-[calc(100vh-111px)]"
        defaultValue="list"
        value={activeTab}
        onChange={setActiveTab}
      >

        {/* Tab Header */}
        <div className="w-full px-6 border-b border-gray-200 flex items-center justify-between py-3 shadow bg-white">
          <div className="flex items-center gap-6">
            <button
              type="button"
              className="flex items-center gap-3 rounded-lg px-3 py-2 hover:cursor-pointer"
              // select list view when this is clicked
              onClick={() => setActiveTab('list')}
            >
              <div className="w-8 h-8 rounded-lg bg-[#F2F4F7] flex items-center justify-center">
                <ArrowLeftIcon size={16} weight="bold" className="text-[#0F1011]" />
              </div>
              <span
                style={{
                  fontFamily: 'Poppins',
                  fontWeight: 700,
                  fontSize: '13.02px',
                  borderBottom: activeTab === 'list' ? '2px solid #002FD4' : 'none',
                  color: activeTab === 'list' ? '#002FD4' : '#0F1011',  
                }}
              >
                Your Schedule
              </span>
            </button>

            <Tabs.List>
              <Tabs.Tab 
                value="services"
                classNames={{
                  tab: `font-poppins font-semibold text-sm ${
                    activeTab === 'services' 
                      ? 'bg-[#002FD4] text-white' 
                      : 'bg-transparent text-[#64748B]'
                  }`
                }}
              >
                Services
              </Tabs.Tab>
            </Tabs.List>
          </div>

          <div className="flex items-center gap-4">
            <ViewToggle
              value={activeTab === 'services' ? 'list' : (activeTab as 'list' | 'calendar')}
              onChange={(v) => setActiveTab(v === 'list' || v === 'calendar' ? v : activeTab)}
            />
          </div>
        </div>

        {/* Main Content Area */}
        <div className="h-full bg-[#F4F6F9]">
          <Card
            h="100%"
            radius="sm"
            className="bg-[#F4F6F9]"
          >
            <Card.Section className="p-4 overflow-auto h-full bg-[#F4F6F9]">
              <Tabs.Panel
                className="h-full"
                value="your_schedule"
              >
                <CalendarSchedule />
              </Tabs.Panel>
              <Tabs.Panel
                className="h-full"
                value="list"
              >
                <CalendarSchedule />
              </Tabs.Panel>
              <Tabs.Panel
                value="services"
                className="h-full"
              >
                <CalendarServices isActive={activeTab === 'services'} />
                <CreateNewService
                  isOpen={isOpen}
                  setIsOpen={setIsOpen}
                />
              </Tabs.Panel>
              <Tabs.Panel
                value="calendar"
                className="h-full"
              >
                <CalendarWeekView />
              </Tabs.Panel>
            </Card.Section>
          </Card>
        </div>
      </Tabs>
    </div>
  )
}

export default CalendarPage