import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import ConfirmDialog from '@/components/orvo/confirm-dialog'
import { useEducations } from '@/features/app/my-profile/hooks/use-educations'
import { Button } from '@mantine/core'
import { PencilIcon, PlusIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { useEducationsStore } from '../../stores/use-educations-store'
import EducationForm from './education-form'

const Educations: FC = (): ReactElement => {
  const { educations, isLoading, isDeleting, error, deleteEducation } =
    useEducations()

  const { showEducationForm, addEducation, editEducation } =
    useEducationsStore()

  const handleDeleteEducation = (educationId: string) => {
    deleteEducation(educationId, {
      onSuccess: () => {
        toast.success('Education deleted successfully')
      },
      onError: (error: Error) => {
        toast.error(`Failed to delete education: ${error.message}`)
      }
    })
  }

  if (isLoading || isDeleting) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <div className="py-4">
      {showEducationForm ? (
        <EducationForm />
      ) : (
        <div className="flex flex-col gap-4">
          {/* Show Add Membership Button */}
          <Button
            variant={'outline'}
            className="w-full"
            onClick={addEducation}
            disabled={isDeleting}
            leftSection={<PlusIcon />}
          >
            Add Education
          </Button>

          {educations.length > 0 &&
            educations.map(({ id, university, degree, year }) => (
              <div className="bg-[#F4F6F9] border-gray-200 px-4 py-2 border rounded flex justify-between items-center">
                <div className="flex flex-col">
                  {`${degree}, ${university}, (${year})`}
                </div>
                <div className="flex items-center justify-between">
                  <Button
                    variant={'ghost'}
                    size={'icon'}
                    onClick={() =>
                      editEducation({
                        id,
                        university,
                        degree,
                        year
                      })
                    }
                    disabled={isDeleting}
                  >
                    <PencilIcon aria-hidden="true" />
                  </Button>
                  <ConfirmDialog
                    title="Delete Education"
                    description="Are you sure you want to delete this education?"
                    disabled={isDeleting || !id}
                    onClickConfirm={() => handleDeleteEducation(id!)}
                  />
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}

export default Educations
