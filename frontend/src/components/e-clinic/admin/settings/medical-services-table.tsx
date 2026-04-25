// src/components/e-clinic/admin/settings/medical-services-table.tsx
import { MagnifyingGlassIcon, X, PencilSimple, Trash } from "@phosphor-icons/react"
import { useMemo, useState } from "react"
import AddMedicalServiceDialog from "./add-medical-service-dialog"
import { Loader } from '@mantine/core'
import ConfirmationModal from '@/components/ui/confirmation-modal'
import { useDeleteMedicalService, useMedicalServices } from "@/pages/app/settings/hooks/use-medical-services"

export default function MedicalServicesTable() {
  const [searchTerm, setSearchTerm] = useState('')
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [selectedServiceId, setSelectedServiceId] = useState<string | null>(null)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [serviceToDelete, setServiceToDelete] = useState<string | null>(null)
  const [serviceToDeleteName, setServiceToDeleteName] = useState<string>("")

  const { data: medicalServices = [], isLoading } = useMedicalServices()
  const deleteMutation = useDeleteMedicalService()

  const filteredServices = useMemo(() => {
    return medicalServices.filter(service =>
      service.name?.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [medicalServices, searchTerm])

  const handleEdit = (id: string) => {
    setSelectedServiceId(id)
    setIsEditModalOpen(true)
  }

  const handleDeleteClick = (id: string, name: string) => {
    setServiceToDelete(id)
    setServiceToDeleteName(name)
    setIsDeleteModalOpen(true)
  }

  const handleConfirmDelete = () => {
    if (serviceToDelete) {
      deleteMutation.mutate(serviceToDelete, {
        onSuccess: () => {
          setIsDeleteModalOpen(false)
          setServiceToDelete(null)
          setServiceToDeleteName("")
        }
      })
    }
  }

  const handleCancelDelete = () => {
    setIsDeleteModalOpen(false)
    setServiceToDelete(null)
    setServiceToDeleteName("")
  }

  const handleCloseModal = () => {
    setIsEditModalOpen(false)
    setSelectedServiceId(null)
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><Loader /></div>
  }

  return (
    <>
      <div className="w-full mt-4">
        {/* Search Bar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6 items-center">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by Speciality Name"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 ${searchTerm ? 'pr-10' : 'pr-4'} py-2 border border-gray-300 rounded-md
                focus:outline-none focus:ring-2 focus:ring-[#002FD4]
                font-poppins font-normal text-[14px] leading-[100%]
                text-black placeholder:text-[#A5ABB3]`}
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-[#F4F6F9] rounded-md transition-colors"
              >
                <X size={16} weight="bold" className="text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[900px] border border-[#E4E5ED] rounded-lg overflow-hidden">
            <table className="w-full table-auto border-collapse">
              <thead className="bg-[#E8EEFD]">
                <tr>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Sr. No.</th>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Speciality Name</th>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Status</th>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-[#E4E5ED] font-poppins font-normal text-[13px] leading-[20px] text-[#0F1011]">
                {filteredServices.map((service, index) => (
                  <tr key={service.id} className="hover:bg-[#F4F6F9] transition-all">
                    <td className="py-4 px-4">
                      {index + 1}
                    </td>
                    <td className="py-4 px-4 font-medium">
                      {service.name || 'N/A'}
                    </td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                        service.status ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {service.status ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3 justify-center">
                        <button
                          onClick={() => handleEdit(service.id)}
                          className="p-2 rounded-full hover:bg-[#F4F6F9] transition-colors"
                          title="Edit Speciality"
                        >
                          <PencilSimple size={16} weight="regular" className="text-gray-600" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(service.id, service.name || 'this speciality')}
                          className="p-2 rounded-full hover:bg-red-50 transition-colors"
                          title="Delete Speciality"
                        >
                          <Trash size={16} weight="regular" className="text-gray-600 hover:text-red-600" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <AddMedicalServiceDialog
        isOpen={isEditModalOpen}
        onClose={handleCloseModal}
        serviceId={selectedServiceId}
      />
      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Speciality"
        message={`Are you sure you want to delete "${serviceToDeleteName}"? This action cannot be undone and may fail if the speciality is still linked to doctors.`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonColor="danger"
        isLoading={deleteMutation.isPending}
      />
    </>
  )
}
