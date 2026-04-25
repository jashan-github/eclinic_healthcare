import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

type AppStore = {
  selectedClinicId: string
  selectedDate: string | null
  setSelectedDate: (date: string | null) => void
  setSelectedClinicId: (clinicId: string) => void
}

export const useAppStore = create<AppStore>()(
  devtools((set) => ({
    selectedClinicId: '',
    selectedDate: new Date(),

    // Actions
    setSelectedDate: (date) => set({ selectedDate: date }),
    setSelectedClinicId: (clinicId) => set({ selectedClinicId: clinicId })
  }))
)
