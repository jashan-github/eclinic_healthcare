import { PROJECT_NAME } from '@/constants'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const getMetaTitle = (pageTitle: string): string => {
  return `${pageTitle} - ${PROJECT_NAME}`
}
