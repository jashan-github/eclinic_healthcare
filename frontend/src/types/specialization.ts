export type Specialization = {
  id: string
  since_year: string
  till_year: string
  code: string
  name: string
  isMajor: boolean
}

export type SpecializationRaw = Omit<
  Specialization,
  'id' | 'since_year' | 'till_year' | 'code'
>
