import { useAuth } from '@/context/auth/auth-context-utils'
import { getMetaTitle } from '@/lib/utils'
import PatientVitalSignsPage from '@/pages/app/patient/vital-signs'
import NotFound from '@/pages/not-found'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(common)/vital-signs')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Vital Signs')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Vital Signs')
  },
  component: function VitalSignsRoute() {
    const { user } = useAuth()
    const roleFromStorage = localStorage.getItem('role')
    const role = (user?.role || roleFromStorage || '')

    if (role !== 'patient') {
      return <NotFound />
    }

    return <PatientVitalSignsPage />
  },
})

