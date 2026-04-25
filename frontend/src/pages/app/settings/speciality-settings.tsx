import HeadSubhead from '@/components/ui/head-subhead'
import Button from '@/components/ui/button'
import { PlusIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'
import MedicalServicesTable from '@/components/e-clinic/admin/settings/medical-services-table'
import AddMedicalServiceDialog from '@/components/e-clinic/admin/settings/add-medical-service-dialog'

const SpecialitySettingsPage: FC = (): ReactElement => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)

  return (
    <div className="h-screen overflow-hidden bg-[#F4F6F9]">
      <div className="p-8 h-full">
        <div className="bg-white rounded-2xl border border-[#E8EEFD] shadow-[6px_7px_20px_0px_#0000001A] h-full flex flex-col">
          <div className="flex justify-between items-center p-6">
            <HeadSubhead
              head={'Speciality Management'}
              subhead={'Manage medical specialities and services'}
            />
            <Button
              variant="secondary"
              size="md"
              onClick={() => setIsAddDialogOpen(true)}
              icon={<PlusIcon size={16} weight="bold" />}
              iconPosition="left"
              className="h-[44px] border-[#002FD4] text-[#002FD4] hover:bg-[#E9F0FF] hover:border-[#002FD4]"
            >
              Add Speciality
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 pt-0">
              <MedicalServicesTable />
            </div>
          </div>
        </div>
      </div>

      <AddMedicalServiceDialog
        isOpen={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
      />
    </div>
  )
}

export default SpecialitySettingsPage
