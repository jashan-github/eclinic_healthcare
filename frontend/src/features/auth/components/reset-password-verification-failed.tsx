import { Button } from '@mantine/core'
import { Link } from '@tanstack/react-router'
import { type FC } from 'react'
import { XCircleIcon } from '@phosphor-icons/react'

const ResetPasswordVerificationFailedPage: FC = () => {
  return (
    <div className="mx-auto flex items-center justify-center p-4 min-h-screen">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-[6px_7px_20px_0px_rgba(0,0,0,0.10)] py-6 px-5 sm:px-6">

          <div className="flex justify-center mb-8">
            <img src="/assets/icons/e-clinic-logo-full.svg" alt="E-Clinic" className="w-[120px] h-auto sm:w-[150px]" />
          </div>

          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <XCircleIcon size={32} weight="fill" className="text-red-600" />
              </div>
            </div>
            <h1 className="font-poppins font-bold text-2xl text-[#0F1011] mb-2">Verification Failed</h1>
            <p className="font-poppins text-sm text-gray-600 mb-1">
              The password reset link is invalid or has expired.
            </p>
            <p className="font-poppins text-sm text-gray-600">
              Please request a new password reset link to continue.
            </p>
          </div>

          <div className="space-y-4">
            <Button
              component={Link}
              to="/auth/forgot-password"
              fullWidth
              size="md"
              className="bg-[#002FD4] h-11 rounded-md font-poppins font-semibold text-sm text-[#F8FAFC] hover:bg-[#0020B0]"
            >
              Request New Reset Link
            </Button>

            <div className="text-center">
              <Link to="/auth/login" className="text-sm text-[#002FD4] font-poppins font-medium hover:underline">
                Back to Login
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResetPasswordVerificationFailedPage

