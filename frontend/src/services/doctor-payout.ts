import axiosInstance from '@/lib/api'

export const DOCTOR_PAYOUTS = {
  CREATE_RAZORPAY_CONTACT: '/v5/doctor/payout/createContact',
  ADD_BANK_DETAILS_TO_RAZORPAY_CONTACT: '/v5/doctor/payout/addBankAccount',
  TOGGLE_FUND_ACCOUNT_STATUS_FOR_DOCTOR:
    '/v5/doctor/payout/toggleFundAccountStatus',
  INITIATE_PAYOUT_TO_DOCTOR: '/v5/doctor/payout/makePayout',
  GET_ALL_RAZORPAY_TRANSACTIONS: '/v5/doctor/payout/getTransactions',
  GET_ALL_RAZORPAY_BANK_ACCOUNTS: '/v5/doctor/payout/getBankAccounts',
  ACTIVATE_BANK_BY_ID: (bankId: string) =>
    `/v5/doctor/payout/makeBankActive/${bankId}`,
  GET_ALL_TRANSACTIONS: '/v5/doctor/payout/fetchTransactions',
  GET_ALL_PAYOUTS: '/v5/doctor/payout/fetchPayouts',
  GET_BANK_DETAILS: '/v5/doctor/payout/fetchBankDetails',
  ADD_PAYOUT_SCHEDULE: '/v5/doctor/payout/payoutSchedule'
}

export const doctorPayout = {
  getAllRazorpayTransactions: async () => {
    return axiosInstance.get(DOCTOR_PAYOUTS.GET_ALL_RAZORPAY_TRANSACTIONS)
  },
  getAllRazorpayLinkedBankAccounts: async () => {
    return axiosInstance.get(DOCTOR_PAYOUTS.GET_ALL_RAZORPAY_BANK_ACCOUNTS)
  },
  addBankDetails: async () => {
    return axiosInstance.post(
      DOCTOR_PAYOUTS.ADD_BANK_DETAILS_TO_RAZORPAY_CONTACT
    )
  },
  createRazorpayContact: async () => {
    return axiosInstance.post(DOCTOR_PAYOUTS.CREATE_RAZORPAY_CONTACT)
  },
  activateBankById: async (bankId: string) => {
    return axiosInstance.post(DOCTOR_PAYOUTS.ACTIVATE_BANK_BY_ID(bankId))
  },
  toggleFundAccountStatus: async () => {
    return axiosInstance.post(
      DOCTOR_PAYOUTS.TOGGLE_FUND_ACCOUNT_STATUS_FOR_DOCTOR
    )
  },
  initiatePayoutToDoctor: async () => {
    return axiosInstance.post(DOCTOR_PAYOUTS.INITIATE_PAYOUT_TO_DOCTOR)
  },
  getAllTransactions: async () => {
    return axiosInstance.get(DOCTOR_PAYOUTS.GET_ALL_TRANSACTIONS)
  },
  getAllPayouts: async () => {
    return axiosInstance.get(DOCTOR_PAYOUTS.GET_ALL_PAYOUTS)
  },
  getBankDetails: async () => {
    return axiosInstance.get(DOCTOR_PAYOUTS.GET_BANK_DETAILS)
  },
  addPayoutSchedule: async () => {
    return axiosInstance.post(DOCTOR_PAYOUTS.ADD_PAYOUT_SCHEDULE)
  }
}
