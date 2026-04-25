import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import ConfirmDialog from '@/components/orvo/confirm-dialog'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { useAwards } from '../../hooks/use-awards'
import { useAwardsStore } from '../../stores/use-awards-store'
import AwardForm from './award-form'
import { Button } from '@mantine/core'
import { PencilIcon, PlusIcon } from '@phosphor-icons/react'

const Awards: FC = (): ReactElement => {
  const { awards, isLoading, isDeleting, error, deleteAward } = useAwards()

  const { showAwardForm, addAward, editAward } = useAwardsStore()

  const handleDeleteAward = (awardId: string) => {
    deleteAward(awardId, {
      onSuccess: () => {
        toast.success('Award deleted successfully')
      },
      onError: (error: Error) => {
        toast.error(`Failed to delete award: ${error.message}`)
      }
    })
  }

  if (isLoading || isDeleting) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <div className="py-4 h-full">
      {showAwardForm ? (
        <AwardForm />
      ) : (
        <div className="flex flex-col gap-4">
          {/* Show Add Membership Button */}
          <Button
            variant={'outline'}
            leftSection={<PlusIcon />}
            className="w-full"
            onClick={addAward}
            disabled={isDeleting}
          >
            Add Award
          </Button>

          {awards.length > 0 &&
            awards.map(({ id, name, year, published_awarded_by }) => (
              <div className="bg-[#F4F6F9] border-gray-200 px-4 py-2 border rounded flex justify-between items-center">
                <div className="flex flex-col">
                  {`${name}, ${published_awarded_by}, (${year})`}
                </div>
                <div className="flex items-center justify-between">
                  <Button
                    variant={'ghost'}
                    size={'icon'}
                    onClick={() =>
                      editAward({
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
                    title="Delete Award"
                    description="Are you sure you want to delete this award?"
                    disabled={isDeleting || !id}
                    onClickConfirm={() => handleDeleteAward(id!)}
                  />
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}

export default Awards
