import type { AuthContextType } from '@/context/auth/auth-context'
import NotFound from '@/pages/not-found'
import { type QueryClient } from '@tanstack/react-query'
import {
  HeadContent,
  Outlet,
  createRootRouteWithContext
} from '@tanstack/react-router'

export type RouterContext = {
  auth: AuthContextType
  queryClient: QueryClient
}

export const Route = createRootRouteWithContext<RouterContext>()({
  head: () => ({
    meta: [
      {
        name: 'description',
        content: 'EClinic Web Application'
      },
      {
        title: 'Home'
      }
    ]
  }),
  component: () => (
    <>
      <HeadContent />
      <Outlet />
    </>
  ),
  notFoundComponent: NotFound
})
