// src/hooks/use-payments.ts
import { useQuery } from '@tanstack/react-query';
import {
  fetchDoctorPayments,
  type DoctorPaymentsResponse,
} from '../services/payments-service';

interface UseDoctorPaymentsParams {
  page?: number;
  perPage?: number;
  period?: 'week' | 'month' | 'custom';
  dateFrom?: string;
  dateTo?: string;
}

export const useDoctorPayments = ({
  page = 1,
  perPage = 20,
  period,
  dateFrom,
  dateTo
}: UseDoctorPaymentsParams = {}) => {
  return useQuery<DoctorPaymentsResponse, Error>({
    queryKey: ['doctor-payments', page, perPage, period, dateFrom, dateTo],
    queryFn: () => fetchDoctorPayments(page, perPage, period, dateFrom, dateTo),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  });
};
