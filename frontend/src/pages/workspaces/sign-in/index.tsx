import { type FC, type ReactElement } from 'react'

// TODO: Workspace sign-in is unimplemented. This page is a placeholder —
// the form, API integration, and auth flow all still need to be built.
// Do not promote to production until that work is scoped and shipped.
const SignIn: FC = (): ReactElement => {
  return (
    <div className="p-8 text-center">
      <h1 className="text-xl font-semibold mb-2">Workspace Sign In</h1>
      <p className="text-sm text-gray-500">
        This page is not yet implemented.
      </p>
    </div>
  )
}

export default SignIn
