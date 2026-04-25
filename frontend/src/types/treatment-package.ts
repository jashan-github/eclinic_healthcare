export type TreatmentPackage = {
  id?: string
  plan_type: 'subscription' | 'treatment'
  pricing_model: 'upfront' | 'per_session'
  active: boolean
  name: string
  total_price: number
  num_sessions: number
  validity_days: number
  family_members: number
  staff_edit_access: boolean
  description: string
  sessions: TreatmentSession[]
}

export type TreatmentSession = {
  id?: string
  session_name: string
  duration: number
  schedule: string
  schedule_date: string
  description: string
}
