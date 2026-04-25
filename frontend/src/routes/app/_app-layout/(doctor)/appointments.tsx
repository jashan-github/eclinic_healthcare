import { getMetaTitle } from '@/lib/utils'
import Appointments from '@/pages/app/appointments'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(doctor)/appointments')({
  loader: () => {
    const roleFromStorage = localStorage.getItem('role');
    const pageTitle = roleFromStorage === 'Patient' ? 'My Appointments' : 'Appointments';
    useHeaderStore.getState().setPageTitle(pageTitle)
  },
  component: Appointments,
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Appointments')
      }
    ]
  })
})
