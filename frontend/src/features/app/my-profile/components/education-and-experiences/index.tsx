import { Tabs } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import Educations from './educations'
import Experiences from './experiences'

const EducationAndExperiences: FC = (): ReactElement => {
  return (
    <Tabs
      defaultValue="education"
      variant={'outline'}
    >
      <Tabs.List grow>
        <Tabs.Tab value="education">Education</Tabs.Tab>
        <Tabs.Tab value="experiences">Experiences</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="education">
        <Educations />
      </Tabs.Panel>
      <Tabs.Panel value="experiences">
        <Experiences />
      </Tabs.Panel>
    </Tabs>
  )
}

export default EducationAndExperiences
