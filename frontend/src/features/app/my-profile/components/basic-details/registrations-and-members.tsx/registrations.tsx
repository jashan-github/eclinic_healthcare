import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import NoDataFound from '@/components/orvo/common/no-data-found'
import ConfirmDialog from '@/components/orvo/confirm-dialog'
import { useRegistrations } from '@/features/app/my-profile/hooks/use-registrations'
import { Button } from '@mantine/core'
import { PencilIcon, PlusIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { useRegistrationStore } from '../../../stores/use-registration-store'
import RegistrationForm from './registration-form'

const Registrations: FC = (): ReactElement => {
  const { registrations, isLoading, isDeleting, error, deleteRegistration } =
    useRegistrations()

  const { showRegistrationForm, addEditRegistration, editRegistration } =
    useRegistrationStore()

  const handleDeleteRegistration = (id: string) => {
    deleteRegistration(id, {
      onSuccess: () => {
        toast.success('Registration deleted successfully')
      },
      onError: (error: Error) => {
        toast.error(`Failed to delete registration: ${error.message}`)
      }
    })
  }

  if (isLoading || isDeleting) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <div className="py-4 h-full">
      {showRegistrationForm ? (
        <RegistrationForm />
      ) : (
        <div className="flex flex-col gap-4">
          {/* Show Add Membership Button */}
          <Button
            variant={'outline'}
            leftSection={<PlusIcon />}
            className="w-full"
            onClick={addEditRegistration}
          >
            Add New Registration
          </Button>

          {registrations.length === 0 && <NoDataFound />}

          {registrations.length > 0 &&
            registrations.map(
              ({
                id,
                registration_number,
                registration_council,
                registration_year
              }) => (
                <div
                  key={id}
                  className="bg-[#F4F6F9] border-gray-200 px-4 py-2 border rounded flex justify-between items-center"
                >
                  <div className="flex font-bold">
                    {`${registration_number},${registration_council} (${registration_year})`}
                  </div>
                  <div className="flex items-center justify-between">
                    <Button
                      variant={'ghost'}
                      size={'icon'}
                      onClick={() =>
                        editRegistration({
                          id,
                          registration_number,
                          registration_council,
                          registration_year
                        })
                      }
                      disabled={isDeleting}
                      aria-label="Edit Registration"
                    >
                      <PencilIcon aria-hidden="true" />
                    </Button>
                    <ConfirmDialog
                      title="Delete Registration"
                      description="Are you sure you want to delete this registration?"
                      disabled={isDeleting || !id}
                      onClickConfirm={() => handleDeleteRegistration(id!)}
                    />
                  </div>
                </div>
              )
            )}
        </div>
      )}
    </div>
  )
}

export default Registrations
