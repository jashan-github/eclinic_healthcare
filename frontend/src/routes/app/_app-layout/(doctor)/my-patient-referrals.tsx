import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import PatientReferral from '@/pages/app/patient-referral'
import { getAllPatientReferrals } from '@/features/app/patient-referral/services/patient-referral-service'
import { queryOptions } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useHeaderStore } from '@/store/use-header-store'
import { getMetaTitle } from '@/lib/utils'

export const Route = createFileRoute(
  '/app/_app-layout/(doctor)/my-patient-referrals'
)({
  component: PatientReferral,
  errorComponent: ErrorWhileFetchingData,
  head: () => ({
    meta: [
      {
        title: getMetaTitle('My Patient Referrals')
      }
    ]
  }),
  loader: async ({ context: { queryClient } }) => {
    useHeaderStore.getState().setPageTitle('My Patient Referrals')
    queryClient.ensureQueryData(
      queryOptions({
        queryKey: ['myPatientReferrals'],
        queryFn: getAllPatientReferrals,
        staleTime: 1000 * 60 * 5
      })
    )
  },
  pendingComponent: GlobalLoader
})
