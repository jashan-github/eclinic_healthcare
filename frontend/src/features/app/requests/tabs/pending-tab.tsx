import RequestsCard from '@/components/e-clinic/doctor/requests/requests-card'
import RequestDialog from '@/components/e-clinic/doctor/requests/request-dialog'
import { type FC, useState } from 'react'
import type { AppointmentRequestNew } from '../services/appointment-request-services'
import { usePendingRequests } from '../hooks/use-appointment-request'
import { useAcceptRequest, useDoctorWaiverSettings, useRejectRequest } from '../hooks/use-request-handle'
import { toast } from 'react-toastify'

interface RequestTabProps {
  searchTerm?: string
  sortAsc?: boolean | null
  consultType?: 'online' | 'offline' | null
}

const PendingTab: FC<RequestTabProps> = ({ searchTerm = '', sortAsc }) => {
  const [selectedRequest, setSelectedRequest] = useState<AppointmentRequestNew | null>(null)
  const [dialogMode, setDialogMode] = useState<'approve' | 'decline'>('approve')

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = usePendingRequests()

  const acceptMutation = useAcceptRequest()
  const rejectMutation = useRejectRequest()
  const { data: waiverData } = useDoctorWaiverSettings()
  const waiverDoctorDecides = (waiverData?.data?.waiver_enabled && waiverData?.data?.waiver_doctor_decides) ?? false
  const waiverChoices = waiverData?.data?.waiver_choices ?? [0, 25, 50, 75, 100]

  const requests = data?.pages.flatMap(page => page.requests) ?? []

  let filteredRequests = requests.filter(req => {
    const q = searchTerm.toLowerCase()

    const matchesSearch =
      req.patient.name.toLowerCase().includes(q) ||
      req.service.name.toLowerCase().includes(q) ||
      req.preferred_date.toLowerCase().includes(q)

    return matchesSearch
  })

  const handleApprove = (req: AppointmentRequestNew) => {
    setSelectedRequest(req)
    setDialogMode('approve')
  }

  const handleDecline = (req: AppointmentRequestNew) => {
    setSelectedRequest(req)
    setDialogMode('decline')
  }

  if (isLoading) return <div className="py-10 text-center">Loading...</div>
  if (isError) return <div className="py-10 text-center text-red-500">Failed to load requests</div>
  if (filteredRequests.length === 0) {
    return <div className="py-10 text-center">No Records Found</div>
  }

  if (sortAsc !== null) {
    filteredRequests = [...filteredRequests].sort((a, b) => {
      const dateA = new Date(a.created_at).getTime()
      const dateB = new Date(b.created_at).getTime()
      return sortAsc ? dateA - dateB : dateB - dateA
    })
  }
  
  return (
    <>
      <div className="space-y-6 px-2 py-4">
        {filteredRequests.map((req) => (
          <RequestsCard
            key={req.id}
            name={req.patient.name}
            gender={req.patient.gender}
            age={req.patient.age}
            reason={req.service.name}
            description={req.patient.desc}
            submittedAt={req.created_at}
            timeAsked={`${req.preferred_date}T${req.preferred_time}`}
            inclinic={req.consultation_mode === 'IN_CLINIC'}
            onApprove={() => handleApprove(req)}
            onDecline={() => handleDecline(req)}
            isPending={true}
          />
        ))}

        {hasNextPage && (
          <button
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="w-full py-3 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            {isFetchingNextPage ? 'Loading more...' : 'Load More'}
          </button>
        )}
      </div>

      {selectedRequest && (
        <RequestDialog
          open={true}
          requestId={selectedRequest.id}
          patientName={selectedRequest.patient.name}
          reason={selectedRequest.service.name}
          requestedTime={`${selectedRequest.preferred_date}T${selectedRequest.preferred_time}`}
          submittedAt={selectedRequest.created_at}
          mode={dialogMode}
          waiverDoctorDecides={waiverDoctorDecides}
          waiverChoices={waiverChoices}
          onClose={() => setSelectedRequest(null)}
          onApprove={(waiverPercent) => {
            acceptMutation.mutate({
              requestId: selectedRequest.id,
              waiverPercent: waiverDoctorDecides ? waiverPercent : undefined,
            }, {
              onSuccess: () => {
                toast.success('Request Approved!')
                setSelectedRequest(null)
              },
              onError: (error: any) => {
                toast.error(error.response?.data?.message || 'Failed to approve request')
              },
            })
          }}
          onDecline={(reason) => {
            rejectMutation.mutate(
              { requestId: selectedRequest.id, payload: { rejection_reason: reason } },
              {
                onSuccess: () => {
                  toast.success('Request Declined!')
                  setSelectedRequest(null)
                },
                onError: () => {
                  toast.error('Failed to decline request')
                },
              }
            )
          }}

        />
      )}
    </>
  )
}

export default PendingTab