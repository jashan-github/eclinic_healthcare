import type { Publication } from '@/types/publication'
import { create } from 'zustand'

interface PublicationState {
  publication: Publication | null
  showPublicationForm: boolean

  addPublication: () => void
  closeShowPublicationForm: () => void
  editPublication: (data: Publication) => void
  processCancel: () => void
}

export const usePublicationsStore = create<PublicationState>((set) => ({
  publication: null,
  showPublicationForm: false,
  // Actions
  addPublication: () =>
    set({
      publication: null,
      showPublicationForm: true
    }),
  closeShowPublicationForm: () =>
    set({
      publication: null,
      showPublicationForm: false
    }),
  editPublication: (data: Publication) => {
    set({
      publication: data,
      showPublicationForm: true
    })
  },
  processCancel: () => {
    set({
      publication: null,
      showPublicationForm: false
    })
  }
}))
