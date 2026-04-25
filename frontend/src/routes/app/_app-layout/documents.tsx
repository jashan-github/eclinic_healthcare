import { getMetaTitle } from '@/lib/utils'
import PatientDocumentsPage from '@/pages/app/patient/documents'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/documents')({
  component: PatientDocumentsPage,
  head: () => ({
    meta: [
      {
        title: getMetaTitle('My Documents')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('My Documents')
  }
})

