import { getMetaTitle } from '@/lib/utils'
import Calendar from '@/pages/app/calendar'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/calendar')({
  component: Calendar,
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Calendar')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Calendar')
  }
})
