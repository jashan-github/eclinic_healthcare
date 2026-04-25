import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import ConfirmDialog from '@/components/orvo/confirm-dialog'
import { Button } from '@mantine/core'
import { PencilIcon, PlusIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { usePublications } from '../../hooks/use-publications'
import { usePublicationsStore } from '../../stores/use-publications-store'
import PublicationForm from './publication-form'

const Publications: FC = (): ReactElement => {
  const { publications, isLoading, isDeleting, error, deletePublication } =
    usePublications()

  const { showPublicationForm, addPublication, editPublication } =
    usePublicationsStore()

  const handleDeletePublication = (awardId: string) => {
    deletePublication(awardId, {
      onSuccess: () => {
        toast.success('Publication deleted successfully')
      },
      onError: (error: Error) => {
        toast.error(`Failed to delete award: ${error.message}`)
      }
    })
  }

  if (isLoading || isDeleting) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <div className="py-4 px-2">
      {showPublicationForm ? (
        <PublicationForm />
      ) : (
        <div className="flex flex-col gap-4">
          {/* Show Add Membership Button */}
          <Button
            variant={'outline'}
            className="w-full"
            leftSection={<PlusIcon />}
            onClick={addPublication}
          >
            Add Publication
          </Button>

          {publications.length > 0 &&
            publications.map(({ id, name, year, published_awarded_by }) => (
              <div className="bg-[#F4F6F9] border-gray-200 px-4 py-2 border rounded flex justify-between items-center">
                <div className="flex flex-col">
                  {`${name}, ${published_awarded_by}, (${year})`}
                </div>
                <div className="flex items-center justify-between">
                  <Button
                    variant={'ghost'}
                    size={'icon'}
                    onClick={() =>
                      editPublication({
                        id,
                        name,
                        year,
                        published_awarded_by
                      })
                    }
                    disabled={isDeleting}
                    aria-label="Edit Award"
                  >
                    <PencilIcon aria-hidden="true" />
                  </Button>
                  <ConfirmDialog
                    title="Delete Publication"
                    description="Are you sure you want to delete this publication?"
                    disabled={isDeleting || !id}
                    onClickConfirm={() => handleDeletePublication(id!)}
                  />
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}

export default Publications
