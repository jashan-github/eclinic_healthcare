import { Tabs } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import AboutYou from './about-you/index.tsx'
import PracticeAreas from './practice-areas.tsx'
import RegistrationsAndMemberships from './registrations-and-members.tsx/index.tsx'
import Specialisations from './specialisations.tsx'

const BasicDetails: FC = (): ReactElement => {
  return (
    <Tabs
      variant={'outline'}
      defaultValue="about-you"
    >
      <Tabs.List grow>
        <Tabs.Tab value="about-you">About You</Tabs.Tab>
        <Tabs.Tab value="specialisations">Specialisations</Tabs.Tab>
        <Tabs.Tab value="registrations-memberships">
          Registrations & Memberships
        </Tabs.Tab>
        <Tabs.Tab value="practice-areas">Practice Areas</Tabs.Tab>
      </Tabs.List>
      <Tabs.Panel value="about-you">
        <AboutYou />
      </Tabs.Panel>
      <Tabs.Panel value="specialisations">
        <Specialisations />
      </Tabs.Panel>
      <Tabs.Panel
        className="pt-5"
        value="registrations-memberships"
      >
        <RegistrationsAndMemberships />
      </Tabs.Panel>
      <Tabs.Panel value="practice-areas">
        <PracticeAreas />
      </Tabs.Panel>
    </Tabs>
  )
}

export default BasicDetails
