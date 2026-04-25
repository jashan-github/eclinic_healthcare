import { Tabs } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import Exterior from './exterior'
import Identity from './identity'
import Interior from './interior'
import WithPatients from './with-patients'

const ClinicPhotos: FC = (): ReactElement => {
  return (
    <Tabs
      variant={'outline'}
      defaultValue="identity"
    >
      <Tabs.List grow>
        <Tabs.Tab value="identity">Identity</Tabs.Tab>
        <Tabs.Tab value="interior">Interior</Tabs.Tab>
        <Tabs.Tab value="exterior">Exterior</Tabs.Tab>
        <Tabs.Tab value="with-patients">With Patients</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="identity">
        <Identity />
      </Tabs.Panel>
      <Tabs.Panel value="interior">
        <Interior />
      </Tabs.Panel>
      <Tabs.Panel value="exterior">
        <Exterior />
      </Tabs.Panel>
      <Tabs.Panel value="with-patients">
        <WithPatients />
      </Tabs.Panel>
    </Tabs>
  )
}

export default ClinicPhotos
