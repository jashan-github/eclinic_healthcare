import api from '@/lib/api'

// Interface for doctor information
export interface DashboardDoctor {
  id: string
  name: string
  specialty: string
  profile_image: string
}

// Interface for service information
export interface DashboardService {
  id: string
  name: string
}

// Interface for upcoming appointment
export interface DashboardAppointment {
  id: string
  doctor: DashboardDoctor
  service: DashboardService
  appointment_date: string
  appointment_time: string
}

// Interface for summary statistics
export interface DashboardSummary {
  upcoming_appointments: number
  documents_uploaded: number
  pending_approvals: number
}

// Interface for recent activity
export interface DashboardActivity {
  id: string
  type: string // e.g., "appointment_confirmed", "document_uploaded"
  icon: string // e.g., "checkmark", "upload"
  message: string
  created_at: string
  metadata?: Record<string, any>
}

// Interface for patient dashboard data
export interface PatientDashboardData {
  summary: DashboardSummary
  upcoming_appointments: DashboardAppointment[]
  recent_activity?: DashboardActivity[] // Note: API uses "recent_activity" not "recent_activities"
}

// Interface for API response
export interface PatientDashboardResponse {
  success: boolean
  message: string
  data: PatientDashboardData
  errors: null | any
}

// GET: Fetch patient dashboard data
export const getPatientDashboard = async (): Promise<PatientDashboardResponse> => {
  try {
    const response = await api.get<PatientDashboardResponse>('/v1/patient/dashboard')
    return response.data
  } catch (error) {
    console.error('Failed to fetch patient dashboard data:', error)
    throw error
  }
}

