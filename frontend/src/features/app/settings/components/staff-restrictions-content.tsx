// components/e-clinic/doctor/settings/staff-restrictions-content.tsx

import { useState, type FC } from 'react'
import { useStaffRestrictions, useUpdateStaffRestrictions } from '@/hooks/use-doctor-settings'
import React from 'react'
import type { StaffRestrictionsData } from '@/services/doctor-settings-service'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { toast } from 'react-toastify'

interface Permission {
  id: string
  label: string
  key: keyof Pick<
    StaffRestrictionsData,
    | 'access_all_patients_page'
    | 'ability_to_start_visit'
    | 'access_payment_page'
    | 'access_download_database'
  >
}

const permissionsConfig: Permission[] = [
  { id: 'all-patients', label: 'Access to All Patients Page', key: 'access_all_patients_page' },
  { id: 'start-visit', label: 'Ability to Start a Visit', key: 'ability_to_start_visit' },
  { id: 'payment-page', label: 'Access to Payment Page', key: 'access_payment_page' },
  { id: 'download-db', label: 'Access to Download Database', key: 'access_download_database' },
]

const StaffRestrictionsContent: FC = () => {
  const { data: restrictions, isLoading, isError } = useStaffRestrictions()
  const { mutate: updateRestrictions, isPending: isSaving } = useUpdateStaffRestrictions()

  const [localPermissions, setLocalPermissions] = useState<Record<string, boolean>>({})

  // Sync local state when data loads
  React.useEffect(() => {
    if (restrictions) {
      setLocalPermissions({
        access_all_patients_page: restrictions.access_all_patients_page,
        ability_to_start_visit: restrictions.ability_to_start_visit,
        access_payment_page: restrictions.access_payment_page,
        access_download_database: restrictions.access_download_database,
      })
    }
  }, [restrictions])

  const togglePermission = (key: string) => {
    setLocalPermissions(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const clinicId = restrictions?.clinic_id
  const hasClinic = !!clinicId

  const handleSave = () => {
    if (!hasClinic) {
      // Defensive: button is already disabled, but guard the API call too so a
      // malformed hardcoded UUID can never reach the backend.
      toast.error('No clinic is assigned to your account.')
      return
    }

    const payload = {
      clinic_id: clinicId,
      ...localPermissions,
    }

    updateRestrictions(payload, {
      onSuccess: () => {
        toast.success('Staff restrictions saved successfully!')
      },
      onError: (error: any) => {
        toast.error(error.message || 'Failed to save changes')
      }
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <GlobalLoader />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="text-center py-10 text-red-600">
        Failed to load staff restrictions. Please try again.
      </div>
    )
  }

  if (!hasClinic) {
    return (
      <div className="mx-auto p-6 bg-white rounded-lg">
        <div className="mb-8">
          <div className="font-poppins font-bold text-base leading-6 tracking-normal text-[#0F1011]">
            Staff Restrictions
          </div>
        </div>
        <div className="border border-[#E4E5ED] rounded-lg p-6 bg-[#FFF7ED] text-[#92400E] font-poppins text-sm">
          You don&apos;t have a clinic assigned yet. Restrictions can&apos;t be configured until an admin assigns
          your account to a clinic.
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto p-6 bg-white rounded-lg">
      <div className="mb-8">
        <div className="font-poppins font-bold text-base leading-6 tracking-normal text-[#0F1011]">
          Staff Restrictions
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg py-1">
        {permissionsConfig.map((permission) => (
          <div
            key={permission.id}
            className="flex items-center justify-between py-4 px-6 bg-white hover:bg-gray-50 transition-colors"
          >
            <span className="font-poppins font-normal text-sm leading-6 tracking-normal text-[#0F1011]">
              {permission.label}
            </span>

            <button
              onClick={() => togglePermission(permission.key)}
              disabled={isSaving}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                localPermissions[permission.key] ? 'bg-[#002FD4]' : 'bg-gray-300'
              } ${isSaving ? 'opacity-70 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition-transform duration-200 ease-in-out ${
                  localPermissions[permission.key] ? 'translate-x-5' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>
        ))}
      </div>

      <div className="mt-10 flex justify-start">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={`flex items-center gap-2 px-6 py-3 bg-[#002FD4] text-white rounded-md hover:bg-[#002bb8] transition-colors disabled:opacity-70 disabled:cursor-not-allowed`}
        >
          {isSaving ? (
            <>
              <span className="font-poppins font-semibold text-sm">Saving...</span>
            </>
          ) : (
            <span className="font-poppins font-semibold text-sm">Save Changes</span>
          )}
        </button>
      </div>
    </div>
  )
}

export default StaffRestrictionsContent