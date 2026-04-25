import type { Experience } from '@/types/experience'
import { create } from 'zustand'

interface ExperienceState {
  experience: Experience | null
  showExperienceForm: boolean

  addExperience: () => void
  closeShowExperienceForm: () => void
  editExperience: (data: Experience) => void
  processCancel: () => void
}

export const useExperiencesStore = create<ExperienceState>((set) => ({
  experience: null,
  showExperienceForm: false,
  // Actions
  addExperience: () =>
    set({
      experience: null,
      showExperienceForm: true
    }),
  closeShowExperienceForm: () =>
    set({
      experience: null,
      showExperienceForm: false
    }),
  editExperience: (data: Experience) => {
    set({
      experience: data,
      showExperienceForm: true
    })
  },
  processCancel: () => {
    set({
      experience: null,
      showExperienceForm: false
    })
  }
}))
