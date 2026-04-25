// patient-data-content.tsx

import { useState, useMemo } from 'react'
import SingleEntry from './single-entry-patient-data'
import { MagnifyingGlassIcon } from '@phosphor-icons/react'
import { TextInput } from '@mantine/core'
import { useStaffPatients } from '@/hooks/use-staff'
import { useDebouncedValue } from '@mantine/hooks'

export default function PatientDataContent() {
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch] = useDebouncedValue(searchQuery, 500)

  // Fetch patients from API
  const { data: patientsData, isLoading, error } = useStaffPatients({
    page: 1,
    per_page: 20,
    search: debouncedSearch || undefined
  })

  // Transform API data to component format
  const patients = useMemo(() => {
    if (!patientsData?.data?.patients) return []
    
    return patientsData.data.patients.map((patient) => ({
      id: patient.id,
      name: patient.name,
      email: patient.email || '',
      age: patient.age || 0,
      gender: patient.gender 
        ? (patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1).toLowerCase()) as 'Male' | 'Female'
        : 'Male' as 'Male' | 'Female',
      contactNumber: patient.contact || 'N/A',
      emergencyContact: patient.emergency_contact || 'N/A',
      familyContact: patient.family_contact || 'N/A'
    }))
  }, [patientsData])

  return (
    <div className="h-full flex flex-col">
      {/* Search */}
      <div className="mb-6 flex-shrink-0">
        <TextInput
          placeholder="Search by patient name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          leftSection={<MagnifyingGlassIcon size={18} weight="bold" />}
          className="flex-1"
          radius="md"
          size="md"
        />
      </div>

      {/* Scrollable List */}
      <div className="flex-1 overflow-y-auto space-y-4 px-1">
        {isLoading ? (
          <div className="text-center py-20 text-gray-500 font-medium h-full flex items-center justify-center">
            Loading patients...
          </div>
        ) : error ? (
          <div className="text-center py-20 text-red-500 font-medium h-full flex items-center justify-center">
            {error.message || 'Failed to load patients'}
          </div>
        ) : patients.length > 0 ? (
          <div className="min-h-full">
            {patients.map((pat) => (
              <SingleEntry
                key={pat.id}
                name={pat.name}
                email={pat.email}
                age={pat.age}
                gender={pat.gender}
                contactNumber={pat.contactNumber}
                emergencyContact={pat.emergencyContact}
                familyContact={pat.familyContact}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-20 text-gray-500 font-medium h-full flex items-center justify-center">
            {searchQuery ? 'No patients match your search' : 'No patients found'}
          </div>
        )}
      </div>
    </div>
  )
}
