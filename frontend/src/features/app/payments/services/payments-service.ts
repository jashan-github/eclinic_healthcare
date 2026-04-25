// src/services/payments-service.ts
import api from '@/lib/api';

export interface PatientDetails {
  id: string;
  name: string;
  phone: string;
}

export interface Service {
  id: string;
  name: string;
}

export interface Transaction {
  id: string;
  serial_number: number;
  patient_details: PatientDetails;
  contact_number: string;
  service: Service;
  amount: number;
  currency: string;
  paymode: string;
  receipt_number: string;
  created_at: string;
}

export interface Pagination {
  current_page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface PaymentsStats {
  total_earned: number;
  growth: number;
  currency: string;
}

export interface DoctorPaymentsResponse {
  stats: PaymentsStats;
  transactions: Transaction[];
  pagination: Pagination;
}

export const fetchDoctorPayments = async (
  page: number = 1,
  perPage: number = 20,
  period?: 'week' | 'month' | 'custom',
  dateFrom?: string,
  dateTo?: string
): Promise<DoctorPaymentsResponse> => {
  try {
    const params: any = {
      page,
      per_page: perPage,
    };

    if (period) {
      params.period = period;
      if (period === 'custom' && dateFrom && dateTo) {
        params.date_from = dateFrom;
        params.date_to = dateTo;
      }
    }

    const response = await api.get(`/v1/doctor/payments/transactions`, { params });
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch doctor payments:', error);
    throw new Error('Unable to load payment transactions');
  }
};