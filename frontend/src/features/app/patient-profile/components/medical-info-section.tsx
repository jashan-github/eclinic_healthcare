import { PlusIcon } from '@phosphor-icons/react'
import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { usePatientMedicalInfo } from '@/hooks/use-patient-medical-info'
import { Modal, TextInput, Button, Group } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'

// Default predefined conditions list (exactly matching backend keys)
const defaultPredefinedConditions = [
  'Diabetes mellitus',
  'Hypertension',
  'Hypothyroidism',
  'Alcohol',
  'Tobacco',
  'Smoke'
]

const MedicalInfoSection = () => {
  const { medicalInfo, updateMedicalInfo, isUpdatingMedicalInfo } = usePatientMedicalInfo()

  // State
  const [medicalConditions, setMedicalConditions] = useState<Array<{ label: string; isActive: boolean; years: string }>>([])
  const [customConditions, setCustomConditions] = useState<Array<{ label: string; isActive: boolean; years: string }>>([])
  const [existingCondition, setExistingCondition] = useState({ condition: '', years: '' })
  const [allergies, setAllergies] = useState({ details: '', years: '' })
  const [medications, setMedications] = useState<Array<{ name: string; dosage: string; frequency: string }>>([{ name: '', dosage: '', frequency: '' }])

  // NEW: For custom condition modal
  const [opened, { open, close }] = useDisclosure(false)
  const [customLabel, setCustomLabel] = useState('')

  // Load data from API
  useEffect(() => {
    if (medicalInfo) {
      // Predefined conditions
      const predefined = defaultPredefinedConditions.map(label => ({
        label,
        isActive: medicalInfo.predefined_conditions?.some(c => c.name === label && c.selected) || false,
        years: medicalInfo.predefined_conditions?.find(c => c.name === label)?.years || ''
      }))
      setMedicalConditions(predefined)

      // Custom conditions
      setCustomConditions(medicalInfo.custom_conditions?.map(c => ({ label: c.name, isActive: true, years: c.years || '' })) || [])

      // Existing condition
      setExistingCondition({
        condition: medicalInfo.existing_condition?.name || '',
        years: medicalInfo.existing_condition?.years || ''
      })

      // Allergies
      setAllergies({
        details: medicalInfo.allergies?.details || '',
        years: medicalInfo.allergies?.years || ''
      })

      // Medications
      if (medicalInfo.medications && medicalInfo.medications.length > 0) {
        setMedications(medicalInfo.medications)
      } else {
        setMedications([{ name: '', dosage: '', frequency: '' }])
      }
    }
  }, [medicalInfo])

  // NEW: Add custom condition handler
  const addCustomCondition = () => {
    if (customLabel?.trim()) {
      setCustomConditions([
        ...customConditions,
        { label: customLabel.trim(), isActive: true, years: '' }
      ])
      setCustomLabel('')
      close()
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="font-poppins font-bold text-[24px] leading-[32px] text-[#0F1011] mb-2">
          Medical Information
        </h2>
        <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
          Update your medical information
        </p>
      </div>

      <form onSubmit={async (e) => {
        e.preventDefault()

        const payload = {
          predefined_conditions: medicalConditions
            .filter(c => c.isActive)
            .map(c => ({
              name: c.label,
              selected: true,
              years: c.years || undefined
            })),
          custom_conditions: customConditions
            .filter(c => c.isActive)
            .map(c => ({
              name: c.label,
              years: c.years || undefined
            })),
          existing_condition: existingCondition.condition || existingCondition.years
            ? {
              name: existingCondition.condition || undefined,
              years: existingCondition.years || undefined
            }
            : undefined,
          allergies: allergies.details || allergies.years
            ? {
              details: allergies.details || undefined,
              years: allergies.years || undefined
            }
            : undefined,
          medications: medications.filter(m => m.name.trim() !== '')
        }

        updateMedicalInfo(payload, {
          onSuccess: () => toast.success('Medical information saved!'),
          onError: () => toast.error('Failed to save medical information')
        })
      }}>
        {/* Pre-defined & Custom Conditions - Combined in same grid for identical styling */}
        <div className="bg-white rounded-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            {/* Predefined Conditions */}
            {medicalConditions.map((condition, index) => (
              <div key={index} className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    const updated = [...medicalConditions]
                    updated[index].isActive = !updated[index].isActive
                    if (!updated[index].isActive) {
                      updated[index].years = ''
                    }
                    setMedicalConditions(updated)
                  }}
                  className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${condition.isActive
                    ? 'bg-[#1F832D]'
                    : 'bg-[#F4F6F9] border border-[#E4E5ED]'
                    }`}
                >
                  {condition.isActive ? (
                    <span className='text-white'>Y</span>
                  ) : (
                    <div className="flex items-center gap-0.5">
                      <div className="w-1 h-1 rounded-full bg-[#0F1011]" />
                      <div className="w-2 h-0.5 bg-[#0F1011]" />
                      <div className="w-1 h-1 rounded-full bg-[#0F1011]" />
                    </div>
                  )}
                </button>
                <span className="font-poppins font-medium text-[14px] text-[#0F1011] flex-1">
                  {condition.label}
                </span>
                <input
                  type="text"
                  value={condition.years}
                  onChange={(e) => {
                    if (condition.isActive) {
                      const updated = [...medicalConditions]
                      updated[index].years = e.target.value
                      setMedicalConditions(updated)
                    }
                  }}
                  placeholder="Years"
                  readOnly={!condition.isActive}
                  disabled={!condition.isActive}
                  className={`w-[97px] px-3 py-1.5 rounded-md border border-[#E4E5ED] 
                    font-poppins text-[14px] font-normal text-[#0F1011] 
                    focus:outline-none transition-colors
                    ${condition.isActive
                      ? 'focus:ring-2 focus:ring-[#E4E1FA] bg-white cursor-text'
                      : 'bg-gray-50 text-gray-500 cursor-not-allowed'}`}
                />
              </div>
            ))}

            {/* Custom Conditions - Exact same styling as predefined */}
            {customConditions.map((condition, index) => (
              <div key={`custom-${index}`} className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    const updated = [...customConditions]
                    updated[index].isActive = !updated[index].isActive
                    if (!updated[index].isActive) {
                      updated[index].years = ''
                    }
                    setCustomConditions(updated)
                  }}
                  className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${condition.isActive
                    ? 'bg-[#1F832D]'
                    : 'bg-[#F4F6F9] border border-[#E4E5ED]'
                    }`}
                >
                  {condition.isActive ? (
                    <span className='text-white'>Y</span>
                  ) : (
                    <div className="flex items-center gap-0.5">
                      <div className="w-1 h-1 rounded-full bg-[#0F1011]" />
                      <div className="w-2 h-0.5 bg-[#0F1011]" />
                      <div className="w-1 h-1 rounded-full bg-[#0F1011]" />
                    </div>
                  )}
                </button>
                <span className="font-poppins font-medium text-[14px] text-[#0F1011] flex-1">
                  {condition.label}
                </span>
                <input
                  type="text"
                  value={condition.years}
                  onChange={(e) => {
                    if (condition.isActive) {
                      const updated = [...customConditions]
                      updated[index].years = e.target.value
                      setCustomConditions(updated)
                    }
                  }}
                  placeholder="Years"
                  readOnly={!condition.isActive}
                  disabled={!condition.isActive}
                  className={`w-[97px] px-3 py-1.5 rounded-md border border-[#E4E5ED] 
                    font-poppins text-[14px] font-normal text-[#0F1011] 
                    focus:outline-none transition-colors
                    ${condition.isActive
                      ? 'focus:ring-2 focus:ring-[#E4E1FA] bg-white cursor-text'
                      : 'bg-gray-50 text-gray-500 cursor-not-allowed'}`}
                />
                <button
                  type="button"
                  onClick={() => setCustomConditions(customConditions.filter((_, i) => i !== index))}
                  className="text-red-500 hover:text-red-700"
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          {/* Add Custom Button - Now opens Mantine Modal */}
          <button
            type="button"
            onClick={open}
            className="flex items-center gap-2 px-3 py-2 rounded-md border border-[#E4E5ED] 
                bg-white hover:bg-[#F4F6F9] transition-colors"
          >
            <div className="w-6 h-6 rounded-full bg-[#002FD4] flex items-center justify-center">
              <PlusIcon size={14} weight="bold" className="text-white" />
            </div>
            <span className="font-poppins font-medium text-[14px] text-[#0F1011]">
              Add Custom
            </span>
          </button>
        </div>

        {/* Existing Condition */}
        <div className="bg-white rounded-lg p-6 mb-6">
          <label className="block mb-3 font-poppins font-medium text-[14px] text-[#545D69]">
            Any existing medical condition?
          </label>
          <div className="flex gap-4">
            <input
              type="text"
              value={existingCondition.condition}
              onChange={(e) => setExistingCondition({ ...existingCondition, condition: e.target.value })}
              placeholder="e.g. Asthma"
              className="flex-1 px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                placeholder:text-[#A5ABB3D9] placeholder:font-medium
                focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
            />
            <input
              type="text"
              value={existingCondition.years}
              onChange={(e) => setExistingCondition({ ...existingCondition, years: e.target.value })}
              placeholder="Years"
              className="w-32 px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                placeholder:text-[#A5ABB3D9] placeholder:font-medium
                focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
            />
          </div>
        </div>

        {/* Allergies */}
        <div className="bg-white rounded-lg p-6 mb-6">
          <label className="block mb-3 font-poppins font-medium text-[14px] text-[#545D69]">
            Allergies (if any)
          </label>
          <div className="flex gap-4">
            <input
              type="text"
              value={allergies.details}
              onChange={(e) => setAllergies({ ...allergies, details: e.target.value })}
              placeholder="e.g. Penicillin, Peanuts"
              className="flex-1 px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                placeholder:text-[#A5ABB3D9] placeholder:font-medium
                focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
            />
            <input
              type="text"
              value={allergies.years}
              onChange={(e) => setAllergies({ ...allergies, years: e.target.value })}
              placeholder="Years"
              className="w-32 px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                placeholder:text-[#A5ABB3D9] placeholder:font-medium
                focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
            />
          </div>
        </div>

        {/* Current Medications */}
        <div className="bg-white rounded-lg p-6 mb-6">
          <label className="block mb-3 font-poppins font-medium text-[14px] text-[#545D69]">
            Current Medications
          </label>
          <div className="space-y-4">
            {medications.map((med, index) => (
              <div key={index} className="flex gap-4">
                <input
                  type="text"
                  value={med.name}
                  onChange={(e) => {
                    const updated = [...medications]
                    updated[index].name = e.target.value
                    setMedications(updated)
                  }}
                  placeholder="Name"
                  className="flex-1 px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                    placeholder:text-[#A5ABB3D9] placeholder:font-medium
                    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
                />
                <input
                  type="text"
                  value={med.dosage}
                  onChange={(e) => {
                    const updated = [...medications]
                    updated[index].dosage = e.target.value
                    setMedications(updated)
                  }}
                  placeholder="Dosage"
                  className="flex-1 px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                    placeholder:text-[#A5ABB3D9] placeholder:font-medium
                    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
                />
                <input
                  type="text"
                  value={med.frequency}
                  onChange={(e) => {
                    const updated = [...medications]
                    updated[index].frequency = e.target.value
                    setMedications(updated)
                  }}
                  placeholder="Frequency"
                  className="flex-1 px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                    placeholder:text-[#A5ABB3D9] placeholder:font-medium
                    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
                />
                {medications.length > 1 && (
                  <button
                    type="button"
                    onClick={() => setMedications(medications.filter((_, i) => i !== index))}
                    className="text-red-500 hover:text-red-700 px-2"
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={() => setMedications([...medications, { name: '', dosage: '', frequency: '' }])}
              className="text-[#002FD4] hover:text-[#001FB8] font-poppins text-sm font-medium"
            >
              + Add Medication
            </button>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8">
          <button
            type="submit"
            disabled={isUpdatingMedicalInfo}
            className="w-[140px] h-11 rounded-lg bg-[#002FD4] text-white font-poppins font-semibold text-sm hover:bg-[#001FB8] transition-colors disabled:opacity-50"
          >
            {isUpdatingMedicalInfo ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>

      {/* NEW: Mantine Modal for Add Custom */}
      <Modal
        opened={opened}
        onClose={close}
        title="Add Custom Condition/Habit"
        centered
        size="sm"
      >
        <TextInput
          label="Enter name"
          placeholder="e.g. Fatty liver"
          value={customLabel}
          onChange={(e) => setCustomLabel(e.currentTarget.value)}
          mb="md"
        />
        <Group justify="flex-end">
          <Button variant="default" onClick={close}>
            Cancel
          </Button>
          <Button color="#002FD4" onClick={addCustomCondition}>
            Add
          </Button>
        </Group>
      </Modal>
    </div>
  )
}

export default MedicalInfoSection