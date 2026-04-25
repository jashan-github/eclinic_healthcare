import MyDoctorNetwork from '@/features/app/patient-referral/components/my-doctor-network'
import PatientReferralFilters from '@/features/app/patient-referral/components/patient-referral-filters'
import { Button } from '@mantine/core'
import { UserIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

const PatientReferral: FC = (): ReactElement => {
  const [isMyDoctorNetworkTabOpen, setIsMyDoctorNetworkTabOpen] =
    useState(false)

  return (
    <div className="h-screen overflow-hidden w-full p-4 bg-white">
      <div className="flex justify-between items-center">
        {/* Patient Referral Filters */}
        <PatientReferralFilters />
        <Button
          variant={'outline'}
          className="text-primary cursor-pointer hover:bg-primary hover:text-white"
          leftSection={<UserIcon />}
          onClick={() => setIsMyDoctorNetworkTabOpen(true)}
        >
          My Healthcare Provider Network (0)
        </Button>
      </div>
      <div className="flex flex-col"></div>
      <MyDoctorNetwork
        isOpen={isMyDoctorNetworkTabOpen}
        onClose={() => setIsMyDoctorNetworkTabOpen(false)}
      />
    </div>
  )
}

export default PatientReferral
