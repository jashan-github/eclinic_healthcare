import { createProfile } from '../services/create-profile-service'
// import type { CreateProfileData } from '../services/create-profile-service'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import { useNavigate } from '@tanstack/react-router'
import { useAuth } from '@/context/auth/auth-context-utils'

export const useCreateProfile = () => {
  const navigate = useNavigate()
  const { user, setUser } = useAuth();

  const mutation = useMutation({
    mutationFn: createProfile,
    onSuccess: () => {
      toast.success('Profile created successfully!')
      if (user) {
        setUser({
          ...user,
          is_completed: true,
          is_profile_complete: true,
        });
      }

      // Check if there's a redirect parameter in the URL
      const urlParams = new URLSearchParams(window.location.search)
      const redirectParam = urlParams.get('redirect')
      
      let redirectTo = redirectParam || '/app/appointments'
      
      // If no redirect param, use role-based routing
      if (!redirectParam) {
        const routeMap: Record<string, string> = {
          admin: '/app/dashboard',
          doctor: '/app/appointments',
          patient: '/app/dashboard',
          staff: '/app/dashboard',
          super_admin: '/app/dashboard',
          clinic_admin: '/app/dashboard'
        }
        const roleFromStorage = localStorage.getItem('role')
        const userRole = (user?.role || roleFromStorage || 'doctor')
        redirectTo = routeMap[userRole] ?? '/app/appointments'
      }
      
      navigate({ to: redirectTo })
    },
    onError: (error: any) => {
      const errorMessage =
        error?.response?.data?.message || 'Failed to create profile'
      toast.error(errorMessage)
      console.error('Failed to create profile:', error)
    }
  })

  return {
    createProfile: mutation.mutate,
    isCreating: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error
  }
}


