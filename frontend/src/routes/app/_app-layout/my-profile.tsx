import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import MyProfile from '@/pages/app/my-profile'
import { getMyProfileDetails } from '@/features/app/my-profile/services/my-profile-service'
import { queryOptions } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useHeaderStore } from '@/store/use-header-store'
import { getMetaTitle } from '@/lib/utils'

export const Route = createFileRoute('/app/_app-layout/my-profile')({
  component: MyProfile,
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

    queryClient.ensureQueryData(
      queryOptions({
        queryKey: ['myProfileDetails'],
        queryFn: getMyProfileDetails,
        staleTime: 1000 * 60 * 5
      })
    )
  },
  pendingComponent: GlobalLoader
})
