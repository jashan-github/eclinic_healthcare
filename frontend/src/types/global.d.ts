export {}

declare global {
  interface Window {
    __LETTERHEAD__: string | {
      type: 'default'
      doctorName: string
      qualification: string
      clinicAddress: string
    } | null
  }
}