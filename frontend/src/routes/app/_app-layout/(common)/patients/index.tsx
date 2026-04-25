import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { useAuth } from '@/context/auth/auth-context-utils'
import { getAllPatients } from '@/features/app/patients/services/patients-service'
import { getMetaTitle } from '@/lib/utils'
import PatientsPage from '@/pages/app/patients'
import NotFound from '@/pages/not-found'
import { useHeaderStore } from '@/store/use-header-store'
import { queryOptions } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(common)/patients/')({
  component: () => {
    const { user } = useAuth()
    const roleFromStorage = localStorage.getItem('role')
    const role = (user?.role || roleFromStorage || '')
    
    if (role !== 'doctor') {
      return <NotFound />
    }

    return <PatientsPage />
  },
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Patients')
      }
    ]
  }),
  errorComponent: ErrorWhileFetchingData,
  loader: async ({ context: { queryClient } }) => {
  useHeaderStore.getState().setPageTitle('Patients (0)')

  await queryClient.ensureQueryData(
    queryOptions({
      queryKey: ['patients', 1],
      queryFn: ({ queryKey }) => {
        const [, pageNum = 1] = queryKey as [string, number?]
        return getAllPatients(pageNum, 20)
      },
      staleTime: 1000 * 60 * 5,
    })
  )
},
  pendingComponent: GlobalLoader
})
