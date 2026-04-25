import { type FC, type ReactElement } from 'react'

type InformationCardProps = {
  title: string
  subtitle: string
  className: string
  onCardClick: () => void
}

const InformationCard: FC<InformationCardProps> = ({
  title,
  subtitle = '-',
  className,
  onCardClick
}): ReactElement => {
  return (
    <div
      className={className}
      onClick={onCardClick}
    >
      <div className="text-sm font-light">{title}</div>
      <div className="text-lg font-bold ">{subtitle}</div>
    </div>
  )
}

export default InformationCard
