import { Drawer, ScrollArea } from '@mantine/core'
import type { FC, ReactElement, ReactNode } from 'react'

interface GlobalFormDrawerProps {
  className?: string
  isOpen: boolean
  onOpenChange: (val: boolean) => void
  title?: string
  children: ReactNode
  size?: string
}

const GlobalFormDrawer: FC<GlobalFormDrawerProps> = ({
  children,
  className,
  isOpen,
  onOpenChange,
  title,
  size = 'lg'
}): ReactElement => {
  return (
    <Drawer
      opened={isOpen}
      onClose={() => onOpenChange(false)}
      position="right"
      size={size}
      className={className}
      title={title}
      scrollAreaComponent={ScrollArea.Autosize}
    >
      {children}
    </Drawer>
  )
}

export default GlobalFormDrawer
