import React from 'react'
import { createLink } from '@tanstack/react-router'
import { Button, type ButtonProps } from '@mantine/core'

// Define props for your custom button link
interface CustomNavLinkProps extends ButtonProps {
  openInNewTab?: boolean
  href?: string // Add href for anchor element
}

// Forward ref to the underlying HTML anchor element
const MantineButtonLinkComponent = React.forwardRef<
  HTMLAnchorElement,
  CustomNavLinkProps
>((props, ref) => (
  <Button
    ref={ref}
    component="a"
    {...props}
  />
))

// Create the TanStack Router compatible Link component
export const CustomNavLink = createLink(MantineButtonLinkComponent)
