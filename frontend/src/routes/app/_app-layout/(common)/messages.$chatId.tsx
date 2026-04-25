import { getMetaTitle } from '@/lib/utils'
import MessagesPage from '@/pages/app/messages'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(common)/messages/$chatId')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Messages')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Messages')
  },
  component: MessagesPage
})