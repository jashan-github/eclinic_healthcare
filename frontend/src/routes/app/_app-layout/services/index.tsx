import { getMetaTitle } from '@/lib/utils'
import ServicesPage from '@/pages/app/admin/services'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/services/')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Services')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Services')
  },
  component: ServicesPage
})
