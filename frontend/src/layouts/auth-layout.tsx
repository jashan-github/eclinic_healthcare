import { Outlet } from '@tanstack/react-router'
import { type FC, type ReactElement } from 'react'
import AuthFooter from './auth-layout/auth-footer'
import AuthHero from './auth-layout/auth-hero'

const AuthLayout: FC = (): ReactElement => {
  return (
    <div className=" min-h-[400px] overflow-y-auto h-screen w-screen overflow-hidden bg-[#F4F6FA] bg-cover bg-center bg-no-repeat bg-[url('/assets/e-clinic/auth-bg.png')]">
      <div className="mx-auto max-w-[1100px] w-full flex flex-col items-center gap-0 px-4 md:px-8 justify-center relative z-10 min-h-screen">
        <AuthHero />

        <div className="w-full flex">
          <Outlet />
        </div>
      </div>

      <AuthFooter />
    </div>
  )
}

export default AuthLayout
