import type { FC, ReactNode } from 'react'
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

type HeaderStore = {
  // State
  pageTitle: string
  selectedClinicId: string
  selectedDate: Date | undefined
  leftContent: FC | ReactNode | null
  rightContent: FC | ReactNode | null
  showHeader: boolean

  // Actions
  setPageTitle: (pageTitle: string) => void
  setSelectedDate: (date: Date | undefined) => void
  setSelectedClinicId: (clinicId: string) => void
  setLeftContent: (content: FC | ReactNode | null) => void
  setRightContent: (content: FC | ReactNode | null) => void
  setShowHeader: (show: boolean) => void
  reset: () => void // New: Reset to defaults
}

const defaultState = {
  leftContent: null,
  rightContent: null,
  pageTitle: 'Salutogena',
  selectedClinicId: '',
  selectedDate: new Date(),
  showHeader: true
}

export const useHeaderStore = create<HeaderStore>()(
  devtools((set) => ({
    ...defaultState,

    // Actions
    setPageTitle: (pageTitle) => set({ pageTitle }),
    setSelectedDate: (date) => set({ selectedDate: date }),
    setSelectedClinicId: (clinicId) => set({ selectedClinicId: clinicId }),
    setLeftContent: (content) => set({ leftContent: content }),
    setRightContent: (content) => set({ rightContent: content }),
    setShowHeader: (show) => set({ showHeader: show }),
    reset: () => set(defaultState)
  }))
)
