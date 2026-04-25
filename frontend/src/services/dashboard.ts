import api from "@/lib/api";

// ─── Stats ─────────────────────────────────────────────────────────

export interface DashboardStats {
  total_revenue: number;
  total_referrals: number;
  total_commissions: number;
  total_webinars_this_month: number;
  currency: string;
}

export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  try {
    const response = await api.get("/v1/admin/dashboard/stats");
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch dashboard stats:", error);
    throw new Error("Unable to load dashboard stats");
  }
};

// ─── Revenue Graph ─────────────────────────────────────────────────

export interface DashboardRevenuePoint {
  year: number;
  month: number;
  month_label: string;
  revenue: number;
}

export const fetchDashboardRevenueGraph = async (
  months = 6,
): Promise<DashboardRevenuePoint[]> => {
  try {
    const response = await api.get("/v1/admin/dashboard/revenue-graph", {
      params: { months },
    });
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch dashboard revenue graph:", error);
    throw new Error("Unable to load revenue graph");
  }
};

// ─── Recent Activity ───────────────────────────────────────────────

export interface RecentActivityItem {
  id: string;
  user_initials: string;
  user_name: string;
  action: string;
  entity_type: string;
  created_at: string;
  time_ago: string;
}

export const fetchDashboardRecentActivity = async (
  limit = 20,
  status = "all",
): Promise<RecentActivityItem[]> => {
  try {
    const response = await api.get("/v1/admin/dashboard/recent-activity", {
      params: { limit, status },
    });
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch recent activity:", error);
    throw new Error("Unable to load recent activity");
  }
};

// ─── Active Appointments ───────────────────────────────────────────

export interface ActiveAppointment {
  id: string;
  doctor_name: string;
  patient_name: string;
  service_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  status: string;
  price_amount: number;
  currency: string;
  invoice_id?: string;
}

export interface ActiveAppointmentsResponse {
  data: ActiveAppointment[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export const fetchDashboardActiveAppointments = async (
  limit = 20,
  status = "all",
): Promise<ActiveAppointmentsResponse> => {
  try {
    const response = await api.get("/v1/admin/dashboard/active-appointments", {
      params: { limit, status },
    });
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch active appointments:", error);
    throw new Error("Unable to load active appointments");
  }
};
