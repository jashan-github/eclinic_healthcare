import { CalendarIcon, CheckCircleIcon, UploadIcon, FilePlusIcon, PrescriptionIcon, CurrencyDollarIcon } from '@phosphor-icons/react'
import { usePatientDashboard } from '@/hooks/use-patient-dashboard'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { formatDate } from '@/utils/helper'
import { Link } from '@tanstack/react-router'

export default function PatientDashboard() {
  const { data: dashboardData, isLoading, error } = usePatientDashboard()

  // Activity type icon mapping
  const getActivityIcon = (type: string) => {
    // Handle various activity types
    if (type.includes('appointment')) {
      return CheckCircleIcon
    }
    if (type.includes('document')) {
      return UploadIcon
    }
    if (type.includes('prescription')) {
      return PrescriptionIcon
    }
    if (type.includes('payment')) {
      return CurrencyDollarIcon
    }
    return FilePlusIcon
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F4F6F9] p-6 flex items-center justify-center">
        <GlobalLoader />
      </div>
    )
  }

  if (error || !dashboardData?.data) {
    return (
      <div className="min-h-screen bg-[#F4F6F9] p-6 flex items-center justify-center">
        <p className="text-red-500 font-poppins text-lg">
          Failed to load dashboard data. Please try again.
        </p>
      </div>
    )
  }

  const { summary, upcoming_appointments, recent_activity = [] } = dashboardData.data

  return (
    <div className="min-h-screen bg-[#F4F6F9] p-6">

      {/* Welcome Message */}
      <div className="mb-8">
        <h1 className="font-poppins font-bold text-[28px] leading-[36px] text-[#0F1011] mb-2">
          Welcome back! Here's your health overview
        </h1>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-2">
            Upcoming Appointments
          </p>
          <p className="font-poppins font-bold text-[32px] leading-[40px] text-[#0F1011]">
            {summary.upcoming_appointments}
          </p>
        </div>
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-2">
            Documents Uploaded
          </p>
          <p className="font-poppins font-bold text-[32px] leading-[40px] text-[#0F1011]">
            {summary.documents_uploaded}
          </p>
        </div>
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-2">
            Pending Approvals
          </p>
          <p className="font-poppins font-bold text-[32px] leading-[40px] text-[#0F1011]">
            {summary.pending_approvals}
          </p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Upcoming Appointments */}
        <div className="lg:col-span-2">
          <div className="mb-4">
            <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#0F1011] mb-1">
              Upcoming Appointments
            </h2>
            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
              Your scheduled consultations
            </p>
          </div>
          {upcoming_appointments.length > 0 ? (
            <div className="space-y-4">
              {upcoming_appointments.map((appointment) => (
                <div key={appointment.id} className="bg-white rounded-lg p-6 shadow-sm">
                  <div className="flex items-start gap-4">
                    {appointment.doctor.profile_image && (
                      <img
                        src={appointment.doctor.profile_image}
                        alt={appointment.doctor.name}
                        className="w-12 h-12 rounded-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = '/assets/icons/doctor-icon.svg'
                        }}
                      />
                    )}
                    <div className="flex-1">
                      <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-1">
                        {appointment.doctor.name}
                      </h3>
                      <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-1">
                        {appointment.doctor.specialty}
                      </p>
                      <p className="font-poppins font-normal text-[12px] leading-[16px] text-[#002FD4] mb-3">
                        {appointment.service.name}
                      </p>
                      <div className="flex items-center gap-2 text-[#64748B]">
                        <CalendarIcon size={16} weight="bold" />
                        <span className="font-poppins font-normal text-[14px] leading-[20px]">
                          {formatDate(appointment.appointment_date)} at {appointment.appointment_time}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg p-6 shadow-sm text-center">
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
                No upcoming appointments
              </p>
            </div>
          )}
        </div>

        {/* Right Column - Quick Actions */}
        <div>
          <div className="mb-4">
            <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#0F1011] mb-1">
              Quick Actions
            </h2>
            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
              Common tasks and services
            </p>
          </div>
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <Link
              to="/app/doctors"
              className="w-full bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold text-[14px] leading-[20px] py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              <CalendarIcon size={20} weight="bold" />
              Book Appointment
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="mt-8">
        <div className="mb-4">
          <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#0F1011] mb-1">
            Recent Activity
          </h2>
          <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
            Your latest health portal activities
          </p>
        </div>
        {recent_activity.length > 0 ? (
          <div className="bg-white rounded-lg p-6 shadow-sm space-y-4">
            {recent_activity.map((activity) => {
              const ActivityIcon = getActivityIcon(activity.type)
              return (
                <div key={activity.id} className="flex items-start gap-4 pb-4 border-b border-[#E4E5ED] last:border-0 last:pb-0">
                  <div className="w-10 h-10 rounded-full bg-[#002FD4] bg-opacity-10 flex items-center justify-center flex-shrink-0">
                    <ActivityIcon size={20} weight="bold" className="text-[#002FD4]" />
                  </div>
                  <div className="flex-1">
                    <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                      {activity.message}
                    </p>
                    <p className="font-poppins font-normal text-[12px] leading-[16px] text-[#64748B] mt-1">
                      {formatDate(activity.created_at)}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="bg-white rounded-lg p-6 shadow-sm text-center">
            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
              No recent activities
            </p>
          </div>
        )}
      </div>

    </div>
  )
}

