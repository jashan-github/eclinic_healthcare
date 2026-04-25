import { Outlet } from '@tanstack/react-router'
import { type FC, type ReactElement } from 'react'
import PublicHeader from './public-header'

const PublicLayout: FC = (): ReactElement => {
  return (
    <div className="min-h-screen w-screen flex flex-col gap-md">
      <PublicHeader />

      <Outlet />
    </div>
  )
}

export default PublicLayout
