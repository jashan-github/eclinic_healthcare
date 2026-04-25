import { Grid, Select } from '@mantine/core'
import { MagnifyingGlassIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

const LabTestSearchLabTestsAndRadiology: FC = (): ReactElement => {
  return (
    <Grid>
      <Grid.Col span={12}>
        <Select
          placeholder="Start typing Lab test/ Radiology"
          data={['CBC', 'RBC', 'Vue', 'Svelte']}
          leftSection={<MagnifyingGlassIcon />}
          rightSection={<></>}
        />
      </Grid.Col>
    </Grid>
  )
}

export default LabTestSearchLabTestsAndRadiology
