import { type FC, type ReactElement } from 'react'
import { ShieldIcon } from '@phosphor-icons/react'
import { SingleCard } from './single-card'

const cards = [
  { id: 1, title: 'Admin', value: 2, Icon: ShieldIcon },
  { id: 2, title: 'Healthcare Provider', value: 18, Icon: ShieldIcon },
  { id: 3, title: 'Staff Members', value: 27, Icon: ShieldIcon }
]

const PermissionsCards: FC = (): ReactElement => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => (
        <SingleCard
          key={c.id}
          title={c.title}
          value={c.value}
          Icon={c.Icon}
        />
      ))}
    </div>
  )
}

export default PermissionsCards
