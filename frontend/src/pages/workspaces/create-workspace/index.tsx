import CreateWorkspaceForm from '@/features/workspaces/components/create-workspace-form'
import WorkspaceHeader from '@/features/workspaces/components/workspace-header'
import { type FC, type ReactElement } from 'react'

const CreateWorkspace: FC = (): ReactElement => {
  return (
    <div className="flex flex-col w-full gap-5">
      {/* Header */}
      <WorkspaceHeader
        title={'Workspace details'}
        subtitle="Your Workspace Name is a way to login to your account on any device."
      />

      {/* Form */}
      <CreateWorkspaceForm />
    </div>
  )
}

export default CreateWorkspace
