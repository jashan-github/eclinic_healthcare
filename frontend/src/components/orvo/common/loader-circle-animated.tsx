import { CircleNotchIcon } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import { type FC, type ReactElement } from 'react'

type LoaderCircleAnimatedProps = {
  size?: number
  className?: string
  text?: string
  textClassName?: string
}

const LoaderCircleAnimated: FC<LoaderCircleAnimatedProps> = ({
  size = 32,
  className,
  text,
  textClassName
}): ReactElement => {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      <CircleNotchIcon
        size={size}
        weight="bold"
        className="animate-spin text-[#002FD4]"
      />
      {text && (
        <p className={cn('font-poppins text-sm text-[#64748B]', textClassName)}>
          {text}
        </p>
      )}
    </div>
  )
}

export default LoaderCircleAnimated
