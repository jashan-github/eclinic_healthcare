// src/services/notifications-service.ts
import api from '@/lib/api'

export interface NotificationItem {
  id: string
  type: string
  title: string
  message: string
  status: string
  is_read: boolean
  appointment_request?: {
    id: string
    patient?: {
      name: string
    }
    doctor?: {
      name: string
    }
    service: {
      name: string
    }
    preferred_date: string
    preferred_time: string
  }
  created_at: string
}

export interface NotificationsResponse {
  notifications: NotificationItem[]
  pagination: {
    current_page: number
    per_page: number
    total: number
    total_pages: number
  }
}

export interface UnreadNotificationCount {
  unread_count: number;
  read_count: number;
  total_count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
  read_count: number;
  total_count: number;
}

export const fetchDoctorNotifications = async (
  page: number = 1,
  limit: number = 20,
  role: string
): Promise<NotificationsResponse> => {
  try {
    const endpoint = role === 'patient'
      ? '/v1/appointment/patient/notifications'
      : '/v1/appointment/doctor/notifications'

    const response = await api.get(endpoint, {
      params: { page, limit },
    })
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch doctor notifications:', error)
    throw new Error('Unable to load notifications')
  }
}

function getNotificationBasePath(role: string): string {
  const normalized = (role || '').toLowerCase();
  return normalized === 'patient'
    ? '/v1/appointment/patient/notifications'
    : '/v1/appointment/doctor/notifications';
}

export const markNotificationAsRead = async (
  notificationId: string,
  role: string
): Promise<void> => {
  const base = getNotificationBasePath(role);
  const url = `${base}/${notificationId}/read`;

  try {
    await api.put(url);
  } catch (err) {
    console.error(`Failed to mark notification ${notificationId} as read`, err);
    throw err;
  }
};

export const markAllNotificationsAsRead = async (role: string): Promise<void> => {
  const base = getNotificationBasePath(role);
  const url = `${base}/read-all`;

  try {
    await api.put(url);
  } catch (err) {
    console.error('Failed to mark all notifications as read', err);
    throw err;
  }
};

export const fetchUnreadNotificationCount = async (
  role: string
): Promise<UnreadCountResponse> => {
  try {
    const base = getNotificationBasePath(role);
    const url = `${base}/unread-count`;

    const response = await api.get(url);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch unread notification count:', error);
    throw new Error('Unable to load unread notification count');
  }
};