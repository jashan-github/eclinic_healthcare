import { cn } from '@/lib/utils'
import { type FC, type ReactElement } from 'react'

type LoaderProps = {
  className?: string
}

const GlobalLoader: FC<LoaderProps> = ({
  className = 'w-[100px]'
}): ReactElement => {
  return (
    <div className="w-full h-full flex items-center justify-center">
      <img
        src="/assets/icons/e-clinic-logo-full.svg"
        alt="Loading..."
        className={cn('animate-pulse', className)}
      />
    </div>
  )
}

export default GlobalLoader
