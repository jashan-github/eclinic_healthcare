import type { Registration } from '@/types/registration'
import { create } from 'zustand'

interface RegistrationState {
  registration: Registration | null
  showRegistrationForm: boolean

  addEditRegistration: () => void
  editRegistration: (data: Registration) => void
  processCancel: () => void
  setRegistration: (data: Registration | null) => void
}

export const useRegistrationStore = create<RegistrationState>((set) => ({
  registration: null,
  showRegistrationForm: false,
  // Actions
  addEditRegistration: () =>
    set({
      registration: null,
      showRegistrationForm: true
    }),
  editRegistration: (data: Registration) => {
    set({
      registration: data,
      showRegistrationForm: true
    })
  },
  processCancel: () => {
    set({
      registration: null,
      showRegistrationForm: false
    })
  },
  setRegistration: (data: Registration | null) => set({ registration: data })
}))
