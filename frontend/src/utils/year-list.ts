export const yearsList = () => {
  const currentYear = new Date().getFullYear() + 30

  return Array.from(
    { length: currentYear - 1911 + 1 },
    (_, i) => currentYear - i
  )
}

export const yearsListTillCurrentYear = () => {
  const currentYear = new Date().getFullYear()

  return Array.from(
    { length: currentYear - 1911 + 1 },
    (_, i) => currentYear - i
  )
}
