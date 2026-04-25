import { getMetaTitle } from '@/lib/utils'
import AnalyticsPage from '@/pages/app/admin/analytics'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(common)/analytics')({
  loader: () => {
    useHeaderStore.getState().setPageTitle('Analytics')
  },
  component: AnalyticsPage,
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Analytics')
      }
    ]
  })
})
