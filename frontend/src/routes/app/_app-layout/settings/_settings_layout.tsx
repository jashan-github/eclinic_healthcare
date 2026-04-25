import SettingsLayout from '@/layouts/settings-layout'
import { getMetaTitle } from '@/lib/utils'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout'
)({
  component: SettingsLayout,
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Settings')
      }
    ]
  })
})
