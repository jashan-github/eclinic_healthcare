import PaymentsHeader from '@/features/app/payments/components/payments-header'
import { useHeaderStore } from '@/store/use-header-store'
import { Check, PencilIcon, TrashIcon, X } from '@phosphor-icons/react'
import { useEffect, useState, type FC, type ReactElement } from 'react'
import { useFees, useUpdateFee } from '@/hooks/use-doctor-settings'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { useDeleteCalendarService } from '../../calendar/hooks/use-calendar-service'
import { toast } from 'react-toastify'
import { useQueryClient } from '@tanstack/react-query'

const FeesSettingsContent: FC = (): ReactElement => {
  const { setRightContent } = useHeaderStore()
  const { data: services = [], isLoading, isError } = useFees()
  const { mutate: updateFee, isPending } = useUpdateFee()
  const deleteMutation = useDeleteCalendarService()
  const queryClient = useQueryClient()
  
  // Editing state
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editPrice, setEditPrice] = useState<string>('')

  const startEdit = (service: typeof services[0]) => {
    setEditingId(service.id)
    setEditPrice(String(service.price))
  }

  const deleteService = (service: typeof services[0]) => {
    if (!confirm('Are you sure you want to delete this service?')) return

    deleteMutation.mutate(service.id, {
      onSuccess: () => {
        // Automatically remove from UI without refresh
        queryClient.setQueryData(['doctor-fees'], (old: typeof services = []) =>
          old.filter(s => s.id !== service.id)
        )
        toast.success('Service deleted successfully')
      },
      onError: () => {
        toast.error('Failed to delete service')
      }
    })
  }

  const saveEdit = (service: typeof services[0]) => {
    const price = Number(editPrice)
    if (isNaN(price) || price < 0) return

    updateFee(
      { id: service.id, data: { price, status: service.status } },
      {
        onSuccess: () => setEditingId(null),
        onError: () => toast.error('Failed to update fee'),
      }
    )
  }

  const toggleStatus = (service: typeof services[0]) => {
    updateFee({ id: service.id, data: { price: service.price, status: !service.status } })
  }

  useEffect(() => {
    setRightContent(PaymentsHeader)
    return () => setRightContent(null)
  }, [setRightContent])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <GlobalLoader />
      </div>
    )
  }

  if (isError) {
    return <div className="text-center py-10 text-red-600">Failed to load fees</div>
  }

  return (
    <div className="mx-auto p-6 bg-white rounded-lg">
      <div className="mb-8 space-y-2">
        <p className="font-poppins font-semibold text-[20px] leading-6 text-[#0F1011]">Fees Settings</p>
        <p className="font-poppins font-normal text-sm leading-5 text-[#64748B]">
          Manage your consultation fees and service pricing
        </p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="grid grid-cols-12 bg-[#E8EEFD] px-6 py-4">
          <div className="col-span-5 font-poppins font-bold text-xs text-[#0F1011]">Service</div>
          <div className="col-span-3 text-center font-poppins font-bold text-xs text-[#0F1011]">Price</div>
          <div className="col-span-2 text-center font-poppins font-bold text-xs text-[#0F1011]">Status</div>
          <div className="col-span-2 text-right font-poppins font-bold text-xs text-[#0F1011]">Action</div>
        </div>

        {services.map((service) => {
          const isEditing = editingId === service.id

          return (
            <div
              key={service.id}
              className="grid grid-cols-12 px-6 py-5 items-center border-t border-gray-100 hover:bg-gray-50 transition-colors"
            >
              <div className="col-span-5">
                <span className="font-poppins font-medium text-sm text-[#0F1011] capitalize">
                  {service.service}
                </span>
              </div>

              <div className="col-span-3 text-center">
                {isEditing ? (
                  <div className="flex items-center justify-center gap-1">
                    <span className="text-gray-600">XCG</span>
                    <input
                      type="number"
                      value={editPrice}
                      onChange={(e) => setEditPrice(e.target.value)}
                      className="w-24 px-2 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-center"
                      autoFocus
                    />
                  </div>
                ) : (
                  <span className="font-poppins font-medium text-sm text-[#0F1011]">₹{service.price}</span>
                )}
              </div>

              <div className="col-span-2 flex justify-center">
                <button
                  onClick={() => toggleStatus(service)}
                  disabled={isPending || isEditing}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${service.status ? 'bg-[#002FD4]' : 'bg-gray-300'
                    } ${isPending || isEditing ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition-transform duration-200 ${service.status ? 'translate-x-5' : 'translate-x-0.5'
                      }`}
                  />
                </button>
              </div>

              <div className="col-span-2 flex justify-end gap-3">
                {isEditing ? (
                  <>
                    <button
                      onClick={() => saveEdit(service)}
                      disabled={isPending}
                      className="text-green-600 hover:text-green-700"
                    >
                      <Check size={20} weight="bold" />
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <X size={20} weight="bold" />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => startEdit(service)}
                    disabled={isPending}
                    className="text-gray-500 hover:text-blue-600 transition-colors"
                    title="Edit Price"
                  >
                    <PencilIcon size={18} />
                  </button>
                )}
                <button
                  onClick={() => deleteService(service)}
                  className="text-gray-500 hover:text-red-500 transition-colors"
                  title="Delete Service"
                >
                  <TrashIcon size={18} />
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {services.length === 0 && (
        <div className="text-center py-10 text-gray-500">No services found</div>
      )}
    </div>
  )
}

export default FeesSettingsContent