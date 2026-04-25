import { type FC, type ReactElement } from 'react'
// import { useAuth } from '@/context/auth/auth-context-utils'
// import AdminWebinar from './admin-webinar'
import DoctorWebinar from './doctor-webinar'

const WebinarsPage: FC = (): ReactElement => {
  // const { user } = useAuth()

  // const role = user?.role?.toLowerCase()

  // if (role === 'doctor') return <DoctorWebinar />
  return <DoctorWebinar />
  // return <AdminWebinar />
}

export default WebinarsPage
