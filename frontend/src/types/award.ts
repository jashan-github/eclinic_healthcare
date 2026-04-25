export type Award = {
  id?: string
  name: string
  year: string
  published_awarded_by: string
}

export type AwardRaw = Omit<Award, 'id'>
