import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import PatientProfile from '@/pages/app/patient/profile'
import { getPatientProfileDetails } from '@/features/app/patient-profile/services/patient-profile-service'
import { queryOptions } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useHeaderStore } from '@/store/use-header-store'
import { getMetaTitle } from '@/lib/utils'

export const Route = createFileRoute('/app/_app-layout/patient-profile')({
  component: PatientProfile,
  errorComponent: ErrorWhileFetchingData,
  head: () => ({
    meta: [
      {
        title: getMetaTitle('My Profile')
      }
    ]
  }),
  loader: async ({ context: { queryClient } }) => {
    useHeaderStore.getState().setPageTitle('My Profile')

    try {
      await queryClient.ensureQueryData(
        queryOptions({
          queryKey: ['patientProfileDetails'],
          queryFn: getPatientProfileDetails,
          staleTime: 1000 * 60 * 5
        })
      )
    } catch (error) {
      // Allow page to load even if profile fetch fails (for new patients)
      console.error('Failed to load patient profile:', error)
    }
  },
  pendingComponent: GlobalLoader
})

