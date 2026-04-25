import { Link } from '@tanstack/react-router'
import type { FC, ReactElement } from 'react'

const Unauthorized: FC = (): ReactElement => {
  return (
    <div className="h-screen min-h-screen flex justify-center items-center bg-secondary">
      <div className="bg-white rounded-3xl shadow w-lg p-6 flex justify-center items-center gap-6 flex-col">
        <h1 className="text-4xl">401: Unauthorized</h1>
        <p>Please log in to access this page.</p>
        <div className="flex justify-center gap-2">
          <Link to={'/auth/login'}>Go to Login</Link>
        </div>
      </div>
    </div>
  )
}

export default Unauthorized
