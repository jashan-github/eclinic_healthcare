import { Button } from '@mantine/core'
import { ArrowLeftIcon } from '@phosphor-icons/react'
import { Link } from '@tanstack/react-router'
import { type FC, type ReactElement } from 'react'

interface WorkspaceHeaderProps {
  showTitle?: boolean
  title?: string
  subtitle?: string
}

const WorkspaceHeader: FC<WorkspaceHeaderProps> = ({
  showTitle = true,
  title = '',
  subtitle = ''
}): ReactElement => {
  return (
    <div className="flex items-center w-full gap-5">
      <Button
        variant={'secondary'}
        className="rounded-full w-10 h-10 cursor-pointer"
      >
        <Link to={'/workspaces/sign-in'}>
          <ArrowLeftIcon />
        </Link>
      </Button>

      {/* Show title only if the showTitle prop is true */}
      {showTitle && (
        <div className="flex flex-col gap-2">
          <div className="text-2xl font-light">{title}</div>
          <div className="text-sm">{subtitle}</div>
        </div>
      )}
    </div>
  )
}

export default WorkspaceHeader
