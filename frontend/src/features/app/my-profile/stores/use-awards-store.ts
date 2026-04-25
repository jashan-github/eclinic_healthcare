import type { Award } from '@/types/award'
import { create } from 'zustand'

interface AwardState {
  award: Award | null
  showAwardForm: boolean

  addAward: () => void
  closeShowAwardForm: () => void
  editAward: (data: Award) => void
  processCancel: () => void
}

export const useAwardsStore = create<AwardState>((set) => ({
  award: null,
  showAwardForm: false,
  // Actions
  addAward: () =>
    set({
      award: null,
      showAwardForm: true
    }),
  closeShowAwardForm: () =>
    set({
      award: null,
      showAwardForm: false
    }),
  editAward: (data: Award) => {
    set({
      award: data,
      showAwardForm: true
    })
  },
  processCancel: () => {
    set({
      award: null,
      showAwardForm: false
    })
  }
}))
