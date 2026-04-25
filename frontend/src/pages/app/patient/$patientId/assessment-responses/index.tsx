import { Card, Grid } from '@mantine/core'
import { type FC, type ReactElement } from 'react'

const AssessmentResponses: FC = (): ReactElement => {
  return (
    <Grid
      h={'100vh'}
      gutter={0}
    >
      <Grid.Col
        h={'100vh'}
        bg={'gray.1'}
        span={4}
      ></Grid.Col>
      <Grid.Col
        h={'100vh'}
        span={8}
      >
        <Card
          h={'100%'}
          radius={0}
          shadow={'lg'}
        ></Card>
      </Grid.Col>
    </Grid>
  )
}

export default AssessmentResponses
