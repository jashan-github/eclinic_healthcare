// src/hooks/use-doctor-webinars.ts
import { useQuery } from '@tanstack/react-query'
import { fetchDoctorWebinars, type WebinarResponse, type DoctorWebinar } from '@/services/webinar-service'

export interface WebinarsTransformed {
  upcomingWebinars: DoctorWebinar[]
  liveWebinars: DoctorWebinar[]
  pastWebinars: DoctorWebinar[]
  allWebinars: DoctorWebinar[]
}

export const useDoctorWebinars = () => {
  return useQuery<WebinarResponse, Error, WebinarsTransformed>({
    queryKey: ['doctor-webinars'],
    queryFn: fetchDoctorWebinars,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    retry: 2,
    select: (data) => {
      const now = new Date();
      const webinars = data.data.webinars;

      const upcoming: DoctorWebinar[] = [];
      const live: DoctorWebinar[] = [];
      const past: DoctorWebinar[] = [];

      webinars.forEach(w => {
        const startDateTime = new Date(`${w.webinar_date}T${w.start_time}`);
        const endDateTime = new Date(`${w.webinar_date}T${w.end_time}`);

        if (w.status === 'live') {
          live.push(w);
          upcoming.push(w)
        } else 
          if (w.status === 'completed' || w.status === 'cancelled') {
          past.push(w);
        } else if (endDateTime < now) {
          past.push(w);
        } else if (startDateTime > now) {
          upcoming.push(w);
        } else {
          // start ≤ now ≤ end → live (even if status scheduled hai)
          live.push(w);
          upcoming.push(w)
        }
      });

      return {
        upcomingWebinars: upcoming,
        liveWebinars: live,
        pastWebinars: past,
        allWebinars: webinars,
      };
    },
  })
}

