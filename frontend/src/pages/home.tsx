import { type FC, type ReactElement } from 'react'

const Home: FC = (): ReactElement => {
  return (
    <div className="min-h-screen h-full flex justify-center bg-secondary items-center">
      {/* Logo */}
      <img
        src="/assets/icons/orvo.svg"
        alt="EClinic"
        className="w-[300px]"
      />
    </div>
  )
}

export default Home
