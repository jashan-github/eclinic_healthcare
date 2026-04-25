import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

type AuthFormData = {
  phone?: string
  phone_code?: string
  loginMethod?: string
  emailOrUsername?: string
  password?: string
  email?: string
  username?: string

  otp?: string
}

type AuthStore = {
  authStep: number
  formData: AuthFormData
  setAuthStep: (step: number) => void
  setFormData: (data: Partial<AuthFormData>) => void
  reset: () => void
}

export const useAuthStore = create<AuthStore>()(
  devtools((set) => ({
    authStep: 1,
    formData: {
      phone: '',
      phone_code: '91',
      loginMethod: 'email',
      emailOrUsername: '',
      password: '',
      email: '',
      username: '',
      otp: ''
    },

    setAuthStep: (authStep: number) => set({ authStep }),

    setFormData: (data: Partial<AuthFormData>) =>
      set((state) => ({
        formData: { ...state.formData, ...data }
      })),

    reset: () =>
      set({
        authStep: 1,
        formData: {
          phone: '',
          phone_code: '91',
          loginMethod: 'email',
          emailOrUsername: '',
          password: '',
          email: '',
          username: '',
          otp: ''
        }
      })
  }))
)
