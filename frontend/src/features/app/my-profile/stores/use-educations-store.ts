import type { Education } from '@/types/education'
import { create } from 'zustand'

interface EducationState {
  education: Education | null
  showEducationForm: boolean

  addEducation: () => void
  closeShowEducationForm: () => void
  editEducation: (data: Education) => void
  processCancel: () => void
}

export const useEducationsStore = create<EducationState>((set) => ({
  education: null,
  showEducationForm: false,
  // Actions
  addEducation: () =>
    set({
      education: null,
      showEducationForm: true
    }),
  closeShowEducationForm: () =>
    set({
      education: null,
      showEducationForm: false
    }),
  editEducation: (data: Education) => {
    set({
      education: data,
      showEducationForm: true
    })
  },
  processCancel: () => {
    set({
      education: null,
      showEducationForm: false
    })
  }
}))
