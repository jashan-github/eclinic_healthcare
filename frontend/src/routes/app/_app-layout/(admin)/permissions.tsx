import { getMetaTitle } from '@/lib/utils'
import Permissions from '@/pages/app/admin/permissions'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(admin)/permissions')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Permissions')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Permissions')
  },
  component: Permissions
})
