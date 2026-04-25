import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import ConfirmDialog from '@/components/orvo/confirm-dialog'
import { useExperiences } from '@/features/app/my-profile/hooks/use-experiences'
import { Button } from '@mantine/core'
import { PencilIcon, PlusIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { useExperiencesStore } from '../../stores/use-experiences-store'
import ExperienceForm from './experience-form'

const Experiences: FC = (): ReactElement => {
  const { experiences, isLoading, isDeleting, error, deleteExperience } =
    useExperiences()

  const { showExperienceForm, addExperience, editExperience } =
    useExperiencesStore()

  const handleDeleteExperience = (experienceId: string) => {
    deleteExperience(experienceId, {
      onSuccess: () => {
        toast.success('Experience deleted successfully')
      },
      onError: (error: Error) => {
        toast.error(`Failed to delete experience: ${error.message}`)
      }
    })
  }

  if (isLoading || isDeleting) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <div className="py-4">
      {showExperienceForm ? (
        <ExperienceForm />
      ) : (
        <div className="flex flex-col gap-4">
          {/* Show Add Membership Button */}
          <Button
            leftSection={<PlusIcon />}
            variant={'outline'}
            className="w-full"
            onClick={addExperience}
            disabled={isDeleting}
          >
            Add Experience
          </Button>

          {experiences.length > 0 &&
            experiences.map(
              ({ id, title, clinic_hospital_name, start_from, end_year }) => (
                <div className="bg-[#F4F6F9] border-gray-200 px-4 py-2 border rounded flex justify-between items-center flex-col">
                  <div className="flex justify-between items-center">
                    <div className="">{title}</div>
                    <div className="flex items-center justify-between">
                      <Button
                        variant={'ghost'}
                        size={'icon'}
                        onClick={() =>
                          editExperience({
                            id,
                            title,
                            clinic_hospital_name,
                            start_from,
                            end_year
                          })
                        }
                        disabled={isDeleting}
                      >
                        <PencilIcon />
                      </Button>
                      <ConfirmDialog
                        title="Delete Experience"
                        description="Are you sure you want to delete this education?"
                        disabled={isDeleting || !id}
                        onClickConfirm={() => handleDeleteExperience(id!)}
                      />
                    </div>
                  </div>
                  <div className="">
                    {`${clinic_hospital_name}, ${start_from}-${end_year}`}
                  </div>
                </div>
              )
            )}
        </div>
      )}
    </div>
  )
}

export default Experiences
