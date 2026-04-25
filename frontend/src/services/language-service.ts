import axiosInstance from '@/lib/api'
import type { Language } from '@/types/language'

export const getAllLanguages = async (): Promise<Language[]> => {
  try {
    const { data } = await axiosInstance.get('/v1/languages/languages')
    console.log("langData",{data}.data.data.languages)
    return {data}.data.data.languages
  } catch (error) {
    console.log(error)

    throw error
  }
}
