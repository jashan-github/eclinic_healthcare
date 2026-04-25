// src/hooks/use-appointment-request.ts

import {
  fetchPendingRequests,
  fetchProcessedRequests,
  type AppointmentRequestsResponse,
} from '../services/appointment-request-services'
import { useInfiniteQuery } from '@tanstack/react-query'

interface UseDoctorRequestsParams {
  searchTerm?: string
}

export const usePendingRequests = ({ searchTerm = '' }: UseDoctorRequestsParams = {}) => {
  return useInfiniteQuery<AppointmentRequestsResponse, Error>({
    queryKey: ['doctor-pending-requests', searchTerm],
    queryFn: ({ pageParam }) => {
      const page = typeof pageParam === 'number' ? pageParam : 1
      return fetchPendingRequests(page, 20, searchTerm || undefined)
    },
    getNextPageParam: (lastPage) => {
      const { current_page, total_pages } = lastPage.pagination
      return current_page < total_pages ? current_page + 1 : undefined
    },
    initialPageParam: 1,
    staleTime: 0,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    retry: 2,
  })
}

export const useProcessedRequests = ({ searchTerm = '' }: UseDoctorRequestsParams = {}) => {
  return useInfiniteQuery<AppointmentRequestsResponse, Error>({
    queryKey: ['doctor-processed-requests', searchTerm],
    queryFn: ({ pageParam }) => {
      const page = typeof pageParam === 'number' ? pageParam : 1
      return fetchProcessedRequests(page, 20, searchTerm || undefined)
    },
    getNextPageParam: (lastPage) => {
      const { current_page, total_pages } = lastPage.pagination
      return current_page < total_pages ? current_page + 1 : undefined
    },
    initialPageParam: 1,
    staleTime: 0,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    retry: 2,
  })
}