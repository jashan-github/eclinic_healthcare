// patients-main-content.tsx
import { type FC, type ReactElement, useState, useEffect } from 'react'
import AccordionRow from './accordian-row'
import { Button, Divider, Input, TextInput } from '@mantine/core'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { usePatientMedicalInfo, useUpdatePatientMedicalInfo } from '@/hooks/use-doctor-patient-medical'
import { PlusIcon, TrashIcon } from '@phosphor-icons/react'
import type { MedicalInfo, CurrentMedication } from '@/services/doctor-patient-medical-service'

interface PatientMainContentProps {
  patientId: string
}

const PatientMainContent: FC<PatientMainContentProps> = ({ patientId }): ReactElement => {
  const { data: medicalData, isLoading, error } = usePatientMedicalInfo(patientId)
  const { mutate: updateMedicalInfo, isPending } = useUpdatePatientMedicalInfo()
  
  const [editedData, setEditedData] = useState<MedicalInfo | null>(null)
  const [hasChanges, setHasChanges] = useState(false)

  // Initialize edited data when medical data loads
  useEffect(() => {
    if (medicalData?.data?.medical_info) {
      const info = medicalData.data.medical_info
      console.log(info, 'info')
      setEditedData({
        diabetes_mellitus_years: info.diabetes_mellitus_years ?? null,
        hypertension_years: info.hypertension_years ?? null,
        hypothyroidism_years: info.hypothyroidism_years ?? null,
        alcohol_years: info.alcohol_years ?? null,
        tobacco_years: info.tobacco_years ?? null,
        smoke_years: info.smoke_years ?? null,
        custom_conditions: info.custom_conditions || [],
        existing_condition: info.existing_condition ?? null,
        existing_condition_years: info.existing_condition_years ?? null,
        allergies: info.allergies ?? null,
        allergies_years: info.allergies_years ?? null,
        current_medications: info.current_medications || []
      })
    }
  }, [medicalData])

  if (isLoading) {
    return <GlobalLoader />
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        Failed to load medical information
      </div>
    )
  }

  const medicalInfo = medicalData?.data?.medical_info

  if (!medicalInfo || !editedData) {
    return (
      <div className="text-center py-8 text-gray-500">
        No medical information available
      </div>
    )
  }

  // Auto-save function
  const autoSave = (updatedData: MedicalInfo) => {
    updateMedicalInfo(
      { patientId, payload: { medical_info: updatedData } },
      {
        onSuccess: () => {
          setHasChanges(false)
        }
      }
    )
  }

  // Handlers
  const toggleCondition = (field: keyof MedicalInfo) => {
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        [field]: prev[field] === null ? 1 : null
      }
      // Auto-save after toggle
      autoSave(newData)
      return newData
    })
  }

  const updateYears = (field: keyof MedicalInfo, value: string) => {
    const numValue = value === '' ? 0 : parseInt(value) || 0
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        [field]: numValue
      }
      setHasChanges(true)
      return newData
    })
  }

  const saveYears = () => {
    if (hasChanges && editedData) {
      autoSave(editedData)
    }
  }

  const addCustomCondition = () => {
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        custom_conditions: [...(prev.custom_conditions || []), { name: '', years: 0 }]
      }
      return newData
    })
  }

  const updateCustomCondition = (index: number, field: 'name' | 'years', value: string | number | null) => {
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        custom_conditions: (prev.custom_conditions || []).map((cond, idx) =>
          idx === index ? { ...cond, [field]: value } : cond
        )
      }
      // Auto-save when editing custom condition
      if (field === 'name' || field === 'years') {
        autoSave(newData)
      }
      return newData
    })
  }

  const removeCustomCondition = (index: number) => {
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        custom_conditions: (prev.custom_conditions || []).filter((_, idx) => idx !== index)
      }
      // Auto-save after removal
      autoSave(newData)
      return newData
    })
  }

  const addMedication = () => {
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        current_medications: [...(prev.current_medications || []), { name: '', dosage: '', frequency: '' }]
      }
      return newData
    })
  }

  const updateMedication = (index: number, field: keyof CurrentMedication, value: string) => {
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        current_medications: (prev.current_medications || []).map((med, idx) =>
          idx === index ? { ...med, [field]: value } : med
        )
      }
      setHasChanges(true)
      return newData
    })
  }

  const saveMedication = () => {
    if (hasChanges && editedData) {
      autoSave(editedData)
    }
  }

  const removeMedication = (index: number) => {
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        current_medications: (prev.current_medications || []).filter((_, idx) => idx !== index)
      }
      // Auto-save after removal
      autoSave(newData)
      return newData
    })
  }

  const updateTextFields = (field: keyof MedicalInfo, value: string | number | null) => {
    setEditedData(prev => {
      if (!prev) return prev
      const newData = {
        ...prev,
        [field]: value
      }
      setHasChanges(true)
      return newData
    })
  }

  const saveTextFields = () => {
    if (hasChanges && editedData) {
      autoSave(editedData)
    }
  }

  // Standard conditions configuration
  const standardConditions = [
    { label: 'Diabetes mellitus', field: 'diabetes_mellitus_years' as keyof MedicalInfo },
    { label: 'Hypertension', field: 'hypertension_years' as keyof MedicalInfo },
    { label: 'Hypothyroidism', field: 'hypothyroidism_years' as keyof MedicalInfo },
    { label: 'Alcohol', field: 'alcohol_years' as keyof MedicalInfo },
    { label: 'Tobacco', field: 'tobacco_years' as keyof MedicalInfo },
    { label: 'Smoke', field: 'smoke_years' as keyof MedicalInfo }
  ]

  return (
    <div>
      {/* Show saving indicator */}
      {isPending && (
        <div className="text-sm text-blue-600 mb-2">Saving...</div>
      )}

      {/* Medical Conditions Grid - 3 columns */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {standardConditions.map((condition, idx) => {
          const yearsValue = editedData[condition.field] as number | null
          const isActive = yearsValue !== null

          return (
            <div key={idx} className="flex items-center gap-2 py-1">
              {/* Y/N Badge - Always clickable */}
              <button
                type="button"
                onClick={() => toggleCondition(condition.field)}
                disabled={isPending}
                className={`font-poppins font-bold text-[16px] leading-[18px] px-2.5 py-1.5 rounded-full flex items-center justify-center min-w-[32px] ${
                  isActive ? 'bg-[#E3F8E6] text-[#1F832D]' : 'bg-[#F4F6F9] text-[#0F1011]'
                } cursor-pointer hover:opacity-80 transition-opacity ${isPending ? 'opacity-50' : ''}`}
              >
                {isActive ? 'Y' : 'N'}
              </button>

              {/* Label */}
              <span className="font-poppins font-medium text-[14px] leading-[24px] text-[#0F1011]">
                {condition.label}
              </span>

              {/* Years Input - Always editable when active */}
              {isActive && (
                <Input
                  type="number"
                  value={yearsValue || ''}
                  onChange={(e) => updateYears(condition.field, e.target.value)}
                  onBlur={saveYears}
                  onKeyDown={(e) => e.key === 'Enter' && saveYears()}
                  placeholder="Years"
                  className="w-20"
                  size="xs"
                  disabled={isPending}
                />
              )}
            </div>
          )
        })}
        
        {/* Custom Conditions - Always editable */}
        {(editedData.custom_conditions || []).map((condition, idx) => (
          <div key={`custom-${idx}`} className="flex items-center gap-2 py-1">
            <TextInput
              value={condition.name}
              onChange={(e) => updateCustomCondition(idx, 'name', e.target.value)}
              onBlur={() => {
                // Only autosave once the user has typed something meaningful —
                // avoids persisting partial values mid-typing.
                if (condition.name?.trim().length >= 2) autoSave(editedData)
              }}
              placeholder="Condition name"
              maxLength={500}
              size="xs"
              className="flex-1"
              disabled={isPending}
            />
            <Input
              type="number"
              value={condition.years || ''}
              onChange={(e) => updateCustomCondition(idx, 'years', e.target.value ? parseInt(e.target.value) : null)}
              placeholder="Years"
              className="w-20"
              size="xs"
              disabled={isPending}
            />
            <Button
              size="xs"
              color="red"
              variant="subtle"
              onClick={() => removeCustomCondition(idx)}
              disabled={isPending}
            >
              <TrashIcon size={16} />
            </Button>
          </div>
        ))}
      </div>

      {/* Add Custom Condition Button - Always visible */}
      <div className="mb-4">
        <Button
          leftSection={<PlusIcon size={16} />}
          onClick={addCustomCondition}
          variant="light"
          size="sm"
          disabled={isPending}
        >
          Add Custom Condition
        </Button>
      </div>

      {/* Accordion Sections - Always editable */}
      <div className="space-y-0">
        <Divider className="border-[#E4E5ED]" />
        <AccordionRow 
          title="Existing Conditions"
          badge={editedData.existing_condition ? 'Y' : 'N'}
          badgeColor={editedData.existing_condition ? 'green' : 'gray'}
        >
          <div className="text-left pl-4 space-y-2">
            <TextInput
              label="Condition"
              value={editedData.existing_condition || ''}
              onChange={(e) => updateTextFields('existing_condition', e.target.value || null)}
              onBlur={saveTextFields}
              placeholder="Enter existing condition"
              maxLength={500}
              disabled={isPending}
            />
            <Input
              type="number"
              value={editedData.existing_condition_years || ''}
              onChange={(e) => updateTextFields('existing_condition_years', e.target.value ? parseInt(e.target.value) : null)}
              onBlur={saveTextFields}
              onKeyDown={(e) => e.key === 'Enter' && saveTextFields()}
              placeholder="Years"
              className="w-32"
              disabled={isPending}
            />
          </div>
        </AccordionRow>
        
        <Divider className="border-[#E4E5ED]" />
        <AccordionRow 
          title="Allergies (medications, food, others)"
          badge={editedData.allergies ? 'Y' : 'N'}
          badgeColor={editedData.allergies ? 'green' : 'gray'}
        >
          <div className="text-left pl-4 space-y-2">
            <TextInput
              label="Allergies"
              value={editedData.allergies || ''}
              onChange={(e) => updateTextFields('allergies', e.target.value || null)}
              onBlur={saveTextFields}
              placeholder="e.g., Penicillin, Peanuts"
              maxLength={500}
              disabled={isPending}
            />
            <Input
              type="number"
              value={editedData.allergies_years || ''}
              onChange={(e) => updateTextFields('allergies_years', e.target.value ? parseInt(e.target.value) : null)}
              onBlur={saveTextFields}
              onKeyDown={(e) => e.key === 'Enter' && saveTextFields()}
              placeholder="Years"
              className="w-32"
              disabled={isPending}
            />
          </div>
        </AccordionRow>
        
        <Divider className="border-[#E4E5ED]" />
        <AccordionRow 
          title="Current Medications"
          badge={(editedData.current_medications || []).length > 0 ? 'Y' : 'N'}
          badgeColor={(editedData.current_medications || []).length > 0 ? 'green' : 'gray'}
        >
          <div className="text-left pl-4 space-y-3">
            {(editedData.current_medications || []).map((medication, idx) => (
              <div key={idx} className="flex gap-2 items-start border-b pb-2 last:border-0">
                <div className="flex-1 space-y-2">
                  <TextInput
                    label="Medication Name"
                    value={medication.name}
                    onChange={(e) => updateMedication(idx, 'name', e.target.value)}
                    onBlur={saveMedication}
                    placeholder="e.g., Aspirin"
                    size="sm"
                    disabled={isPending}
                  />
                  <TextInput
                    label="Dosage"
                    value={medication.dosage}
                    onChange={(e) => updateMedication(idx, 'dosage', e.target.value)}
                    onBlur={saveMedication}
                    placeholder="e.g., 100mg"
                    size="sm"
                    disabled={isPending}
                  />
                  <TextInput
                    label="Frequency"
                    value={medication.frequency}
                    onChange={(e) => updateMedication(idx, 'frequency', e.target.value)}
                    onBlur={saveMedication}
                    placeholder="e.g., Once daily"
                    size="sm"
                    disabled={isPending}
                  />
                </div>
                <Button
                  size="sm"
                  color="red"
                  variant="subtle"
                  onClick={() => removeMedication(idx)}
                  className="mt-6"
                  disabled={isPending}
                >
                  <TrashIcon size={16} />
                </Button>
              </div>
            ))}
            <Button
              leftSection={<PlusIcon size={16} />}
              onClick={addMedication}
              variant="light"
              size="sm"
              disabled={isPending}
            >
              Add Medication
            </Button>
          </div>
        </AccordionRow>
        <Divider className="border-[#E4E5ED]" />
      </div>
    </div>
  )
}

export default PatientMainContent