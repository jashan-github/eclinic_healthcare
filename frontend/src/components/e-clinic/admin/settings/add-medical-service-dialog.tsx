// src/components/e-clinic/admin/settings/add-medical-service-dialog.tsx
import React, { useState, useEffect } from 'react'
import { useCreateMedicalService, useUpdateMedicalService, useMedicalServiceById } from '@/pages/app/settings/hooks/use-medical-services'
import Modal from '@/components/ui/modal'
import FormInput from '@/components/ui/form-input'
import Button from '@/components/ui/button'
import { Loader, Switch } from '@mantine/core'
import { toast } from 'react-toastify'

const MAX_SPECIALITY_NAME_LENGTH = 255

interface AddMedicalServiceDialogProps {
  isOpen: boolean
  onClose: () => void
  serviceId?: string | null
}

const AddMedicalServiceDialog: React.FC<AddMedicalServiceDialogProps> = ({ isOpen, onClose, serviceId }) => {
  const isUpdateMode = !!serviceId
  const createMutation = useCreateMedicalService()
  const updateMutation = useUpdateMedicalService()
  const { data: serviceData, isLoading: isLoadingService } = useMedicalServiceById(serviceId || null)

  const [formData, setFormData] = useState({
    name: '',
    status: true,
  })

  useEffect(() => {
    if (serviceData && isUpdateMode && !isLoadingService) {
      setFormData({
        name: serviceData.name || '',
        status: serviceData.status,
      })
    } else if (!isUpdateMode) {
      setFormData({
        name: '',
        status: true,
      })
    }
  }, [serviceData, isUpdateMode, isLoadingService])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleStatusToggle = (checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      status: checked
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const trimmedName = formData.name.trim()
    if (!trimmedName) {
      toast.error('Speciality name is required')
      return
    }
    if (trimmedName.length > MAX_SPECIALITY_NAME_LENGTH) {
      toast.error(`Speciality name must be ${MAX_SPECIALITY_NAME_LENGTH} characters or fewer`)
      return
    }

    const payload = {
      name: trimmedName,
      status: formData.status,
    }

    if (isUpdateMode && serviceId) {
      updateMutation.mutate({ id: serviceId, payload }, { onSuccess: onClose })
    } else {
      createMutation.mutate(payload, { onSuccess: onClose })
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending || isLoadingService

  const footer = (
    <>
      <Button
        type="button"
        variant="primary"
        size="md"
        onClick={handleSubmit}
        disabled={isPending || !formData.name.trim()}
      >
        {isPending
          ? (isUpdateMode ? 'Updating...' : 'Adding...')
          : (isUpdateMode ? 'Update Speciality' : 'Add Speciality')}
      </Button>
      <Button
        type="button"
        variant="secondary"
        size="md"
        onClick={onClose}
        disabled={isPending}
      >
        Cancel
      </Button>
    </>
  )

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isUpdateMode ? "Edit Speciality" : "Add New Speciality"}
      footer={footer}
      maxWidth="md"
    >
      {isLoadingService ? (
        <div className="flex items-center justify-center py-12">
          <Loader />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput
            label="Speciality Name"
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            maxLength={MAX_SPECIALITY_NAME_LENGTH}
            required
          />

          <div>
            <label className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] block mb-2">
              Status
            </label>
            <div className="flex items-center gap-3">
              <Switch
                checked={formData.status}
                onChange={(e) => handleStatusToggle(e.currentTarget.checked)}
                color="#002FD4"
                size="md"
              />
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
                {formData.status ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </form>
      )}
    </Modal>
  )
}

export default AddMedicalServiceDialog
