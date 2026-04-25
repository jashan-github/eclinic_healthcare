import { Tabs } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import Memberships from './memberships'
import Registrations from './registrations'

const registrationsAndMembershipsTabs = [
  {
    label: 'Registrations',
    value: 'registrations',
    component: <Registrations />
  },
  {
    label: 'Memberships',
    value: 'memberships',
    component: <Memberships />
  }
]

const RegistrationsAndMemberships: FC = (): ReactElement => {
  return (
    <Tabs
      variant={'outline'}
      defaultValue="registrations"
    >
      <Tabs.List grow>
        {registrationsAndMembershipsTabs.map(({ label, value }) => (
          <Tabs.Tab
            key={value}
            value={value}
          >
            {label}
          </Tabs.Tab>
        ))}
      </Tabs.List>

      {registrationsAndMembershipsTabs.map(({ value, component }) => (
        <Tabs.Panel
          key={value}
          value={value}
        >
          {component}
        </Tabs.Panel>
      ))}
    </Tabs>
  )
}

export default RegistrationsAndMemberships
