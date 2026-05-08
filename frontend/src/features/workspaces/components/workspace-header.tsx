import { ActionIcon } from '@mantine/core'
import { ArrowLeftIcon } from '@phosphor-icons/react'
import { useRouter } from '@tanstack/react-router'
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
  const router = useRouter()

  const handleBack = () => {
    if (window.history.length > 1) {
      router.history.back()
    } else {
      router.navigate({ to: '/workspaces/sign-in' })
    }
  }

  return (
    <div className="flex items-center w-full gap-5">
      <ActionIcon
        variant="default"
        size={40}
        radius="xl"
        onClick={handleBack}
        aria-label="Go back"
      >
        <ArrowLeftIcon />
      </ActionIcon>

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
