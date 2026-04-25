import BaseSideSheet from '@/components/orvo/base-side-sheet'
import { Button, Input, Stack } from '@mantine/core'
import { type FC, type ReactElement, useState } from 'react'
import { toast } from 'react-toastify'
import { useCreateService } from '@/hooks/use-create-service'  // <-- ye hi add kiya

interface CreateNewServiceProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  onServiceCreated?: (serviceName: string) => void
}

const CreateNewServiceCategory: FC<CreateNewServiceProps> = ({
  isOpen,
  setIsOpen,
  onServiceCreated
}): ReactElement => {
  const [serviceName, setServiceName] = useState('')

  const createServiceMutation = useCreateService()

  const handleCreate = async () => {
    if (!serviceName.trim()) {
      toast.error('Service name is required')
      return
    }

    createServiceMutation.mutate(
      { name: serviceName },
      {
        onSuccess: (newService) => {
          onServiceCreated?.(newService.service_name)
          setServiceName('')
          setIsOpen(false)
        }
      }
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleCreate()
    }
  }

  return (
    <BaseSideSheet
      size="lg"
      title="Create New Service"
      isOpen={isOpen}
      onOpenChange={setIsOpen}
    >
      <Stack gap="lg" pt={'md'} justify='end'>
        <Input
          onChange={(e) => setServiceName(e.currentTarget.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type new service"
          style={{ maxWidth: '100%' }}
        />
        <Button
          type="submit"
          fullWidth
          onClick={handleCreate}
          loading={createServiceMutation.isPending}
          disabled={createServiceMutation.isPending || !serviceName.trim()}
        >
          Create Service
        </Button>
      </Stack>
    </BaseSideSheet>
  )
}

export default CreateNewServiceCategory