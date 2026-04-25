import { Tabs } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import Awards from './awards'
import Publications from './publications'

const AwardsAndPublications: FC = (): ReactElement => {
  return (
    <Tabs
      defaultValue="education"
      variant={'outline'}
    >
      <Tabs.List grow>
        <Tabs.Tab value="education">Awards</Tabs.Tab>
        <Tabs.Tab value="experiences">Publications</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="education">
        <Awards />
      </Tabs.Panel>
      <Tabs.Panel value="experiences">
        <Publications />
      </Tabs.Panel>
    </Tabs>
  )
}

export default AwardsAndPublications
