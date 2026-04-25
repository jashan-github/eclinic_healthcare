import ServicesTable from '@/components/e-clinic/admin/services/services-table'
import CreateNewService from '@/components/e-clinic/doctor/calendar/create-new-service'
import HeadSubhead from '@/components/ui/head-subhead'
import Button from '@/components/ui/button'
import { PlusIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

const ServicesPage: FC = (): ReactElement => {
  const [isCreateServiceOpen, setIsCreateServiceOpen] = useState(false)
  return (
    <div className="h-screen overflow-hidden bg-[#F4F6F9]">
      <div className="p-8 h-full">
        <div className="bg-white rounded-2xl border border-[#E8EEFD] shadow-[6px_7px_20px_0px_#0000001A] h-full flex flex-col">
          <div className="flex justify-between items-center p-6">
            <HeadSubhead
              head={'Service Management'}
              subhead={'Manage service types, pricing, and durations'}
            />
            <Button
              variant="secondary"
              size="md"
              onClick={() => { setIsCreateServiceOpen(true) }}
              icon={<PlusIcon size={16} weight="bold" />}
              iconPosition="left"
              className="h-[44px] border-[#002FD4] text-[#002FD4] hover:bg-[#E9F0FF] hover:border-[#002FD4]"
            >
              Add Service
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 pt-0">
              <ServicesTable />
            </div>
          </div>
        </div>
        <CreateNewService
          isOpen={isCreateServiceOpen}
          setIsOpen={setIsCreateServiceOpen}
        />
      </div>
    </div>
  )
}

export default ServicesPage
