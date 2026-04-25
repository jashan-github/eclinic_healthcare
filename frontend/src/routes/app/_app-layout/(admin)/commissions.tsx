import { getMetaTitle } from '@/lib/utils'
import Commissions from '@/pages/app/admin/commissions'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(admin)/commissions')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Commissions')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Commissions')
  },
  component: Commissions
})
