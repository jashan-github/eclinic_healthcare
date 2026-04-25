import axiosInstance from '@/lib/api'
import type { Membership } from '@/types/membership'
import { z } from 'zod'

const MembershipSchema = z.object({
  id: z.string().optional(),
  organization_name: z.string(),
  member_from: z.string(),
  member_till: z.string()
})

export const getAllMemberships = async (): Promise<Membership[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/profile/memberships')

    return z.array(MembershipSchema).parse(data.data)
  } catch (error) {
    console.log(error)
    throw error
  }
}

export const saveMembership = async (data: Membership): Promise<Membership> => {
  try {
    const validatedData = MembershipSchema.parse(data)

    const { data: response } = await axiosInstance.post(
      '/v5/doctor/profile/memberships',
      validatedData
    )

    return response.data
  } catch (error) {
    console.log(error)
    throw error
  }
}

export const updateMembership = async (
  registrationId: string,
  data: Membership
): Promise<void> => {
  try {
    await axiosInstance.put(
      `/v5/doctor/profile/memberships/${registrationId}`,
      data
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deleteMembership = async (membershipId: string): Promise<void> => {
  try {
    await axiosInstance.delete(`/v5/doctor/profile/memberships/${membershipId}`)
  } catch (error) {
    console.log(error)
    throw error
  }
}
