import HeadSubhead from '@/components/ui/head-subhead'
import Button from '@/components/ui/button'
import { PlusIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'
import VitalsTable from '@/components/e-clinic/admin/settings/vitals-table'
import AddVitalDialog from '@/components/e-clinic/admin/settings/add-vital-dialog'

const VitalsPage: FC = (): ReactElement => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)

  return (
    <div className="h-screen overflow-hidden bg-[#F4F6F9]">
      <div className="p-8 h-full">
        <div className="bg-white rounded-2xl border border-[#E8EEFD] shadow-[6px_7px_20px_0px_#0000001A] h-full flex flex-col">
          <div className="flex justify-between items-center p-6">
            <HeadSubhead
              head={'Vitals Management'}
              subhead={'Manage vital signs templates and defaults'}
            />
            <Button
              variant="secondary"
              size="md"
              onClick={() => setIsAddDialogOpen(true)}
              icon={<PlusIcon size={16} weight="bold" />}
              iconPosition="left"
              className="h-[44px] border-[#002FD4] text-[#002FD4] hover:bg-[#E9F0FF] hover:border-[#002FD4]"
            >
              Add Vital
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 pt-0">
              <VitalsTable />
            </div>
          </div>
        </div>
      </div>

      <AddVitalDialog
        isOpen={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
      />
    </div>
  )
}

export default VitalsPage