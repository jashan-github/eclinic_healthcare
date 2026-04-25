import { Tabs } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import ClinicAmenities from './clinic-amenities'
import ClinicDetails from './clinic-details'
import ClinicPhotos from './clinic-photos'

const ClinicOrPracticeDetails: FC = (): ReactElement => {
  return (
    <Tabs
      variant={'outline'}
      defaultValue="basic-details"
    >
      <Tabs.List grow>
        <Tabs.Tab value="basic-details">Basic Details</Tabs.Tab>
        <Tabs.Tab value="clinic-amenities">Clinic Amenities</Tabs.Tab>
        <Tabs.Tab value="clinic-photos">Clinic Photos</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="basic-details">
        <ClinicDetails />
      </Tabs.Panel>
      <Tabs.Panel value="clinic-amenities">
        <ClinicAmenities />
      </Tabs.Panel>
      <Tabs.Panel
        className="pt-5"
        value="clinic-photos"
      >
        <ClinicPhotos />
      </Tabs.Panel>
    </Tabs>
  )
}

export default ClinicOrPracticeDetails
