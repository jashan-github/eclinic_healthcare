import { Drawer, ScrollArea } from '@mantine/core'
import type { FC, ReactElement, ReactNode } from 'react'

interface BaseSideSheetProps {
  className?: string
  isOpen: boolean
  onOpenChange: (val: boolean) => void
  title?: string
  children: ReactNode
  size?: string | number
}

const BaseSideSheet: FC<BaseSideSheetProps> = ({
  children,
  className,
  isOpen,
  onOpenChange,
  size = 'lg',
  title
}): ReactElement => {
  return (
    <Drawer
      className={className}
      closeOnClickOutside={false}
      onClose={() => onOpenChange(false)}
      opened={isOpen}
      overlayProps={{ backgroundOpacity: 0.5, blur: 4 }}
      position="right"
      scrollAreaComponent={ScrollArea.Autosize}
      size={size}
      title={title}
    >
      {children}
    </Drawer>
  )
}

export default BaseSideSheet
