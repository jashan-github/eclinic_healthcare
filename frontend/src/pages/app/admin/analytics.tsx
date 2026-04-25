import { useAuth } from '@/context/auth/auth-context-utils'
import AdminAnalyticsContent from '@/features/app/calendar/components/analytics/admin-analytics-content'
import DoctorAnalyticsContent from '@/features/app/calendar/components/analytics/doctor-analytics-content'
import NotFound from '@/pages/not-found'
import { type FC, type ReactElement } from 'react'
// import SettingsPage from './settings'

const AnalyticsPage: FC = (): ReactElement => {
  const { user } = useAuth()
  const role = user?.role || localStorage.getItem('role')
  
  // Check if user is admin (super_admin, clinic_admin, or admin)
  const isAdmin = role === 'super_admin' || role === 'clinic_admin' || role === 'admin'
  const isDoctor = role === 'doctor'
  
  if (!isDoctor && !isAdmin) {
    return <NotFound />
  }

  return (
    <div className={`h-full overflow-auto ${isDoctor ? 'bg-white' : 'bg-[#F4F6F9]'}`}>
      {isDoctor ? <DoctorAnalyticsContent /> : <AdminAnalyticsContent />}
    </div>
  )
}

export default AnalyticsPage
