import RequestsCard from '@/components/e-clinic/doctor/requests/requests-card'
import RequestDialog from '@/components/e-clinic/doctor/requests/request-dialog'
import { type FC, useState } from 'react'
import type { AppointmentRequestNew } from '../services/appointment-request-services'
import { useProcessedRequests } from '../hooks/use-appointment-request'
import { toast } from 'react-toastify'

interface RequestTabProps {
  searchTerm?: string
  sortAsc?: boolean | null
}

const ProcessedTab: FC<RequestTabProps> = ({ searchTerm = '', sortAsc }) => {
  const [selectedRequest, setSelectedRequest] = useState<AppointmentRequestNew | null>(null)

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useProcessedRequests({ searchTerm: '' })

  const requests = data?.pages.flatMap(page => page.requests) ?? []

  let filteredRequests = requests.filter(req => {
    const q = searchTerm.toLowerCase()

    return (
      req.patient.name.toLowerCase().includes(q) ||
      req.service.name.toLowerCase().includes(q) ||
      req.preferred_date.toLowerCase().includes(q)
    )
  })

  const handleViewDetails = (req: AppointmentRequestNew) => {
    setSelectedRequest(req)
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
            onApprove={() => handleViewDetails(req)}
            onDecline={() => toast.error('This request is already processed.')}
          isPending={false}
          />
        ))}

        {hasNextPage && (
          <button
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="w-full py-3 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
          >
            {isFetchingNextPage ? 'Loading more...' : 'Load More'}
          </button>
        )}

        {requests.length === 0 && !isLoading && (
          <div className="text-center py-10 text-gray-500">
            No processed requests found
          </div>
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
          mode="approve"
          onClose={() => setSelectedRequest(null)}
          onApprove={() => {
            toast.error('This appointment is already processed.')
            setSelectedRequest(null)
          }}
        />
      )}
    </>
  )
}

export default ProcessedTab