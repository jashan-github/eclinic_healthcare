import CreateProfileForm from '@/features/workspaces/components/create-profile-form'
import WorkspaceHeader from '@/features/workspaces/components/workspace-header'

import { type FC, type ReactElement } from 'react'

const CreateProfile: FC = (): ReactElement => {
  return (
    <div className="flex flex-col w-full gap-5">
      {/* Header */}
      <WorkspaceHeader
        title={'Create Profile'}
        subtitle="Help us maintain our medical community's integrity with verified credentials."
      />

      {/* Form */}
      <CreateProfileForm />
    </div>
  )
}

export default CreateProfile
