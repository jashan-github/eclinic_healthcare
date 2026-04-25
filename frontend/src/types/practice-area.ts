export type PracticeArea = {
  id: string
  name: string
  status: boolean
  created_at: string
  updated_at: string
}

export type PracticeAreaCompact = Pick<PracticeArea, 'id' | 'name'>
