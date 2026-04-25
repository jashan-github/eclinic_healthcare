import Modal from '@/components/ui/modal'
import { useQuery } from '@tanstack/react-query'
import { Loader } from '@mantine/core'
import api from '@/lib/api'

interface ViewServiceModalProps {
  serviceId: string | null
  isOpen: boolean
  onClose: () => void
}

const ViewServiceModal = ({ serviceId, isOpen, onClose }: ViewServiceModalProps) => {
  const { data: service, isLoading } = useQuery({
    queryKey: ['service', serviceId],
    queryFn: async () => {
      if (!serviceId) return null
      const res = await api.get(`/v1/admin/services/${serviceId}`)
      return res.data.data
    },
    enabled: isOpen && !!serviceId,
  })

  if (!isOpen || !serviceId) return null

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatMinutesToHours = (minutes?: number) => {
    if (!minutes) return '0 hours'
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours === 0) return `${mins} minutes`
    if (mins === 0) return `${hours} hour${hours > 1 ? 's' : ''}`
    return `${hours} hour${hours > 1 ? 's' : ''} ${mins} minute${mins > 1 ? 's' : ''}`
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Service Details"
      maxWidth="2xl"
    >
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader />
        </div>
      ) : service ? (
        <div className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                Service Name
              </label>
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {service.name || 'N/A'}
              </p>
            </div>
            <div>
              <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                Nickname
              </label>
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {service.nickname || 'N/A'}
              </p>
            </div>
            <div>
              <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                Service Mode
              </label>
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {service.service_mode === 'IN_CLINIC' ? 'In-Clinic' : service.service_mode === 'TELECONSULTATION' ? 'Teleconsultation' : service.service_mode}
              </p>
            </div>
            <div>
              <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                Appointment Type
              </label>
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {service.appointment_type || 'N/A'}
              </p>
            </div>
            <div>
              <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                Price
              </label>
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {service.price === 0 || !service.price ? 'Free' : `$${service.price}`}
              </p>
            </div>
            <div>
              <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                Payment Type
              </label>
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {service.payment_type || 'N/A'}
              </p>
            </div>
            <div>
              <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                Status
              </label>
              <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                service.is_bookable
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {service.is_bookable ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div>
              <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                Currency
              </label>
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {service.currency || 'USD'}
              </p>
            </div>
          </div>

          {/* Booking Settings */}
          <div className="border-t border-[#E4E5ED] pt-4">
            <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-4">
              Booking Settings
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                  Advance Booking Days
                </label>
                <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                  {service.advance_booking_days || 0} days
                </p>
              </div>
              <div>
                <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                  Minimum Notice
                </label>
                <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                  {formatMinutesToHours(service.minimum_notice_minutes)}
                </p>
              </div>
            </div>
          </div>

          {/* Timestamps */}
          <div className="border-t border-[#E4E5ED] pt-4">
            <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-4">
              Timestamps
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                  Created At
                </label>
                <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                  {formatDate(service.created_at)}
                </p>
              </div>
              <div>
                <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#64748B] block mb-1">
                  Updated At
                </label>
                <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                  {formatDate(service.updated_at)}
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400 font-poppins">
          Service not found
        </div>
      )}
    </Modal>
  )
}

export default ViewServiceModal

