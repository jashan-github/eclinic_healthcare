import { getMetaTitle } from '@/lib/utils'
import Locations from '@/pages/app/admin/locations'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(admin)/locations')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Locations')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Locations')
  },
  component: Locations
})
