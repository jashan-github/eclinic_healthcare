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
        <h2 className="text-sm font-semibold">
          {isEditing ? 'Edit My Profile' : 'Profile View'}
        </h2>
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
