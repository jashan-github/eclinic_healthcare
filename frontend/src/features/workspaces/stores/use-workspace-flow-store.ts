import { create } from 'zustand'

// Persists step-1 form values across the create-workspace → create-profile
// navigation so the user doesn't lose what they entered when they advance.
// Cleared on flow completion (step 2 submit success) or when the layout
// unmounts via clearWorkspaceFlow().
export interface WorkspaceFlowStep1 {
  salutation: 'Mr' | 'Ms' | 'Dr'
  firstName: string
  middleName: string
  lastName: string
  gender: 'male' | 'female' | 'other'
  dob: string
  countryCode: string
  mobile: string
  email: string
}

interface WorkspaceFlowState {
  step1: WorkspaceFlowStep1 | null
  setStep1: (values: WorkspaceFlowStep1) => void
  clearWorkspaceFlow: () => void
}

export const useWorkspaceFlowStore = create<WorkspaceFlowState>((set) => ({
  step1: null,
  setStep1: (values) => set({ step1: values }),
  clearWorkspaceFlow: () => set({ step1: null }),
}))
