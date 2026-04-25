import AddLocationDialog from '@/components/e-clinic/admin/location/add-location-dialog'
import LocationCards from '@/components/e-clinic/admin/location/location-cards'
import HeadSubhead from '@/components/ui/head-subhead'
import { PlusIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

const LocationsPage: FC = (): ReactElement => {
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  return (
    <>
      <div className="h-screen overflow-auto bg-[#F4F6F9]">
        <div className="p-4 h-full">
          <div className="flex justify-between items-center p-6">
            <HeadSubhead
              head={'Clinic Locations'}
              subhead={'Manage your clinic branches and facilites'}
            />
            <button
              onClick={() => setIsDialogOpen(true)}
              className="hover:cursor-pointer h-[44px] rounded-md border border-[#002FD4] flex items-center justify-center gap-[7px] px-[17px] py-[2px] text-[#002FD4]"
            >
              <PlusIcon size={16} weight="bold" />
              <span className="font-poppins font-semibold text-[13px] leading-[20px] text-nowrap">
                Add Location
              </span>
            </button>
          </div>
          <LocationCards />
        </div>
      </div>
      <AddLocationDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
      />
    </>
  )
}

export default LocationsPage
