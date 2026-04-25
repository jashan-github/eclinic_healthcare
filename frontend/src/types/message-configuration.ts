export type Charges = {
  app: string
  sms: string
  whatsapp: string
}

export type NotificationChannel = {
  disabled: boolean
  isChecked: boolean
  changeAble: boolean
}

export type ListingItem = {
  id: string
  notification_title: string
  description: string
  firebase: NotificationChannel
  whatsapp: NotificationChannel
  sms: NotificationChannel
  toggleStatus: boolean
}

export type NotificationConfig = {
  charges: Charges
  listing: ListingItem[]
}
