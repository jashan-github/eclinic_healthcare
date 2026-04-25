import { SingleCard } from '@/components/e-clinic/staff/dashboard/single-card'
import AppointmentManagement from '@/features/app/staff/components/appointment-management'
import { useStaffStats } from '@/hooks/use-staff'
import { useMemo } from 'react'
import type { StaffStatsData } from '@/services/staff.service'

export default function StaffDashboard() {
    // Fetch dashboard statistics from API
    const { data: statsData } = useStaffStats()

    // Transform API data to card format
    const cards = useMemo(() => {
        const stats: StaffStatsData = statsData?.data || {
            today_appointments_count: 0,
            active_patients_count: 0,
            pending_appointment_requests_count: 0
        }

        return [
            { id: 1, title: 'Todays Appointment', value: stats.today_appointments_count || 0 },
            { id: 2, title: 'Active Patients', value: stats.active_patients_count || 0 },
            { id: 3, title: 'Pending Confirmations', value: stats.pending_appointment_requests_count || 0 },
        ]
    }, [statsData])

    return (
        <div className="min-h-screen bg-[#F4F6F9] p-6">
            {/* Welcome Message */}
            <div className="mb-8">
                <h1 className="font-poppins text-lg font-medium leading-6 text-[#0F1011] align-middle">
                    Welcome back!
                </h1>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {cards.map((c) => (
                    <SingleCard key={c.id} title={c.title} value={c.value} Icon={null} />
                ))}
            </div>

            {/* Appointment Management */}
            <div className='bg-white p-6 mt-10 rounded-lg shadow-[6px_7px_20px_0px_#0000001A] flex flex-col h-[700px]'>
                <div className="font-poppins text-xl font-semibold leading-6 text-[#0F1011]">
                    Appointment Management
                </div>
                <div className="font-poppins text-sm text-slate-500 mt-1 mb-6">
                    Schedule coordination and patient communication
                </div>

                <div className="flex-1 min-h-0">
                    <AppointmentManagement />
                </div>
            </div>
        </div>
    )
}

