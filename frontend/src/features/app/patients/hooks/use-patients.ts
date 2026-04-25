
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { getAllPatients } from '@/features/app/patients/services/patients-service'
import type { Patient } from '@/features/app/patients/services/patients-service'

interface PatientsApiResponse {
  patients: Patient[]
  pagination: {
    total: number
    page: number
    per_page: number
    total_pages: number
  }
}

export const usePatients = () => {
  const [page, setPage] = useState(1)
  const perPage = 20

  const {
    data: response,
    isLoading,
    error,
    isFetching,
  } = useQuery<PatientsApiResponse>({
    queryKey: ['patients', page],
    queryFn: async ({ queryKey }) => {
      const [, pageNum] = queryKey as [string, number]
      return await getAllPatients(pageNum, perPage)
    },
    placeholderData: (prev) => prev,
    staleTime: 5 * 60 * 1000,
  })

  const patients = response?.patients ?? []
  const totalPages = response?.pagination.total_pages ?? 1

  return {
    patients,
    isLoading,
    error,
    isFetching,
    page,
    setPage,
    totalPages,
  }
}