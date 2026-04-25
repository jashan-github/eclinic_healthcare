import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import NoDataFound from '@/components/orvo/common/no-data-found'
import ConfirmDialog from '@/components/orvo/confirm-dialog'
import { useMemberships } from '@/features/app/my-profile/hooks/use-memberships'
import { Button } from '@mantine/core'
import { PencilIcon, PlusIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { useMembershipStore } from '../../../stores/use-membership-store'
import MembershipForm from './membership-form'

const Memberships: FC = (): ReactElement => {
  const { memberships, isLoading, isDeleting, error, deleteMembership } =
    useMemberships()

  const { showMembershipForm, addEditMembership, editMembership } =
    useMembershipStore()

  const handleDeleteMembership = (membershipId: string) => {
    deleteMembership(membershipId, {
      onSuccess: () => {
        toast.success('Membership deleted successfully')
      },
      onError: (error: Error) => {
        toast.error(`Failed to delete membership: ${error.message}`)
      }
    })
  }

  if (isLoading || isDeleting) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <div className="py-4 h-full">
      {showMembershipForm ? (
        <MembershipForm />
      ) : (
        <div className="flex flex-col gap-4">
          {/* Show Add Membership Button */}
          <Button
            variant={'outline'}
            leftSection={<PlusIcon />}
            className="w-full"
            onClick={addEditMembership}
          >
            Add New Membership
          </Button>

          {memberships.length === 0 && <NoDataFound />}

          {memberships.length > 0 &&
            memberships.map(
              ({ id, organization_name, member_from, member_till }) => (
                <div className="bg-[#F4F6F9] border-gray-200 px-4 py-2 border rounded flex justify-between items-center">
                  <div className="flex flex-col">
                    <div className="font-bold">{organization_name},</div>
                    <div className="">{`${member_from}-${member_till}`}</div>
                  </div>
                  <div className="flex items-center justify-between">
                    <Button
                      variant={'ghost'}
                      size={'icon'}
                      onClick={() =>
                        editMembership({
                          id,
                          organization_name,
                          member_from,
                          member_till
                        })
                      }
                      disabled={isDeleting}
                      aria-label="Edit Membership"
                    >
                      <PencilIcon aria-hidden="true" />
                    </Button>
                    <ConfirmDialog
                      title="Delete Membership"
                      description="Are you sure you want to delete this membership?"
                      disabled={isDeleting || !id}
                      onClickConfirm={() => handleDeleteMembership(id!)}
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

export default Memberships
