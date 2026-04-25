import { createFileRoute } from '@tanstack/react-router'
import Users from '@/pages/app/admin/users'
import { useHeaderStore } from '@/store/use-header-store'
import { getMetaTitle } from '@/lib/utils'

export const Route = createFileRoute('/app/_app-layout/(admin)/users')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Users')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Users')
  },
  component: Users
})
