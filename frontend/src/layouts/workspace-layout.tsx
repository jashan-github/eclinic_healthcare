import { Card } from '@mantine/core'
import { Outlet } from '@tanstack/react-router'
import { type FC, type ReactElement } from 'react'

const WorkspaceLayout: FC = (): ReactElement => {
  return (
    <div className="font-montserrat w-screen h-screen bg-secondary overflow-hidden flex items-center justify-center">
      <Card className="w-3xl max-w-3xl">
        <Card.Section className="p-5">
          <Outlet />
        </Card.Section>
      </Card>
    </div>
  )
}

export default WorkspaceLayout
