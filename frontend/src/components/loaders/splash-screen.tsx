import { type FC, type ReactElement } from 'react'

const SplashScreen: FC = (): ReactElement => {
  return (
    <div className="min-h-screen h-full flex justify-center items-center bg-white">
      {/* Logo */}
      <img
        src="/assets/icons/e-clinic-logo.svg"
        alt="E-Clinic"
        className="w-[300px] animate-bounce"
      />
    </div>
  )
}

export default SplashScreen
