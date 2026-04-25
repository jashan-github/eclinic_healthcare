export type Publication = {
  id?: string
  name: string
  year: string
  published_awarded_by: string
}

export type PublicationRaw = Omit<Publication, 'id'>
