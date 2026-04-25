// src/components/e-clinic/admin/vitals/add-vital-dialog.tsx
import React, { useState, useEffect } from 'react'
import { useCreateVital, useUpdateVital, useVitalById } from '@/pages/app/settings/hooks/use-admin-vitals'
import Modal from '@/components/ui/modal'
import FormInput from '@/components/ui/form-input'
import Button from '@/components/ui/button'
import { Loader } from '@mantine/core'

interface AddVitalDialogProps {
  isOpen: boolean
  onClose: () => void
  vitalId?: string | null
}

const AddVitalDialog: React.FC<AddVitalDialogProps> = ({ isOpen, onClose, vitalId }) => {
  const isUpdateMode = !!vitalId
  const createMutation = useCreateVital()
  const updateMutation = useUpdateVital()
  const { data: vitalData, isLoading: isLoadingVital } = useVitalById(vitalId || null)

  const [formData, setFormData] = useState({
    name: '',
    unit: '',
    data_type: 'number', // default value
    is_active: true,
  })

  useEffect(() => {
    if (vitalData && isUpdateMode && !isLoadingVital) {
      setFormData({
        name: vitalData.name,
        unit: vitalData.unit || '',
        data_type: vitalData.data_type || 'number',
        is_active: vitalData.is_active,
      })
    } else if (!isUpdateMode) {
      setFormData({
        name: '',
        unit: '',
        data_type: 'number',
        is_active: true,
      })
    }
  }, [vitalData, isUpdateMode, isLoadingVital])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'is_active' ? value === 'true' : value
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const payload = {
      name: formData.name.trim(),
      unit: formData.unit.trim(),
      data_type: formData.data_type.trim() || 'number',
      is_active: formData.is_active,
    }

    if (isUpdateMode && vitalId) {
      updateMutation.mutate({ id: vitalId, payload }, { onSuccess: onClose })
    } else {
      createMutation.mutate(payload, { onSuccess: onClose })
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending || isLoadingVital

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
          : (isUpdateMode ? 'Update Vital' : 'Add Vital')}
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
      title={isUpdateMode ? "Edit Vital" : "Add New Vital"}
      footer={footer}
      maxWidth="md"
    >
      {isLoadingVital ? (
        <div className="flex items-center justify-center py-12">
          <Loader />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput
            label="Vital Name"
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />

          <FormInput
            label="Unit (e.g., mmHg, bpm, °C, kg)"
            type="text"
            name="unit"
            value={formData.unit}
            onChange={handleChange}
          />

          {/* Data Type as free text input */}
          <FormInput
            label="Data Type"
            type="text"
            name="data_type"
            value={formData.data_type}
            onChange={handleChange}
            placeholder="e.g., number, text, select"
            required
          />

          <div>
            <label className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] block mb-2">
              Status
            </label>
            <select
              name="is_active"
              value={formData.is_active.toString()}
              onChange={handleChange}
              className="w-full px-4 py-2.5 border border-[#E4E5ED] rounded-md focus:outline-none focus:ring-2 focus:ring-[#002FD4] focus:border-[#002FD4] font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]"
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
        </form>
      )}
    </Modal>
  )
}

export default AddVitalDialog