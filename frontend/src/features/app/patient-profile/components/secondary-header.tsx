import { ActionIcon, Button } from '@mantine/core'
import { ArrowLeftIcon, PencilSimpleIcon } from '@phosphor-icons/react'
import { type FC } from 'react'

interface SecondaryHeaderProps {
  isEditing: boolean
  setIsEditing: (value: boolean) => void
  onBack: () => void
}

const SecondaryHeader: FC<SecondaryHeaderProps> = ({
  isEditing,
  setIsEditing,
  onBack
}) => {
  const handleBack = () => {
    if (isEditing) {
      setIsEditing(false)
    } else {
      onBack()
    }
  }

  return (
    <header className="flex h-15 items-center justify-between bg-white px-4 py-2">
      <div className="flex items-center gap-3">
        <ActionIcon
          size="lg"
          radius="xl"
          variant="filled"
          color="gray.2"
          onClick={handleBack}
        >
          <ArrowLeftIcon
            color="black"
            size={18}
            weight="bold"
          />
        </ActionIcon>
        <div>
          <h2 className="text-base font-semibold font-poppins text-[#0F1011]">
            {isEditing ? 'Edit My Profile' : 'My Profile'}
          </h2>
          {isEditing && (
            <p className="text-sm font-normal font-poppins text-[#64748B]">
              Manage your personal information and account settings.
            </p>
          )}
        </div>
      </div>

      {!isEditing && (
        <Button
          leftSection={<PencilSimpleIcon size={18} />}
          variant="outline"
          onClick={() => setIsEditing(true)}
        >
          Edit Profile
        </Button>
      )}
    </header>
  )
}

export default SecondaryHeader

