import type { Membership } from '@/types/membership'
import { create } from 'zustand'

interface MembershipState {
  membership: Membership | null
  showMembershipForm: boolean

  addEditMembership: () => void
  editMembership: (data: Membership) => void
  processCancel: () => void
  setMembership: (data: Membership | null) => void
}

export const useMembershipStore = create<MembershipState>((set) => ({
  membership: null,
  showMembershipForm: false,
  // Actions
  addEditMembership: () =>
    set({
      membership: null,
      showMembershipForm: true
    }),
  editMembership: (data: Membership) => {
    set({
      membership: data,
      showMembershipForm: true
    })
  },
  processCancel: () => {
    set({
      membership: null,
      showMembershipForm: false
    })
  },
  setMembership: (data: Membership | null) => set({ membership: data })
}))
