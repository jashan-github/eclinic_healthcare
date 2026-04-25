import type { UserRoleType } from "@/utils/user-role";

// types/user.ts
export interface AuthenticatedUser {
  is_completed?: boolean;
  isCompleted?: boolean;
  avatar?: string;
  id: string;
  email: string;
  name?: string;
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  phone?: string | null;
  phone_code?: number;
  phone_number?: string | null;
  role: UserRoleType;
  doctor_code?: string;

  is_active?: boolean;
  is_profile_complete?: boolean;
  is_verified?: boolean;

  hipaa_form_filled?: boolean;

  clinic_id?: string | null;
  short_description?: string;
  experience?: string;
  education?: string;
  gender?: string;
  profile_img?: string;
  isWritingPad?: boolean | null;
  total_credits?: number;
  availableCredits?: number;
  available_credits?: boolean;

  created_at?: string;
  updated_at?: string;
}
