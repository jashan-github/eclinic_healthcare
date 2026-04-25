import { type FC, type ReactElement } from 'react'

const AuthFooter: FC = (): ReactElement => {
  return (
    <div className="absolute left-6 bottom-6 z-20 flex items-center gap-4">
      <a
        href="/contact"
        className="font-poppins text-sm font-normal leading-5 text-[#002FD4] no-underline"
      >
        Contact
      </a>
      <a
        href="/terms-and-conditions"
        className="font-poppins text-sm font-normal leading-5 text-[#002FD4] no-underline"
      >
        T&C
      </a>
      <a
        href="/privacy-policy"
        className="font-poppins text-sm font-normal leading-5 text-[#002FD4] no-underline"
      >
        Privacy Policy
      </a>
    </div>
  )
}

export default AuthFooter
