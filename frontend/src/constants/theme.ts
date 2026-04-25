import { createTheme, type MantineColorsTuple } from '@mantine/core'

const primary: MantineColorsTuple = [
  '#e9efff',
  '#d0daff',
  '#9db2fc',
  '#6887fb',
  '#3d63fa',
  '#244cfb',
  '#1840fc',
  '#0b33e1',
  '#002fd4',
  '#0026b1'
]

export const theme = createTheme({
  primaryColor: 'primary',
  colors: {
    primary
  },
  fontFamily: 'Poppins'
})
