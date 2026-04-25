import { GlobeIcon, GraduationCapIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { useMyProfile } from '../../hooks/use-my-profile'

const ExperienceAndLanguages: FC = (): ReactElement => {
  const { myProfile } = useMyProfile()

  return (
    <div className="bg-white rounded border-gray-300 border px-4 py-4 flex items-center justify-between gap-2">
      <div className="flex gap-2 items-start ">
        <GraduationCapIcon size={20} />
        <div className="">
          <div className="text-sm font-bold">{`${myProfile.years_of_experience} Yrs`}</div>
          <div className="text-xs text-muted-foreground">
            Overall Experience
          </div>
        </div>
      </div>
      <div className="flex gap-2 items-start">
        <GlobeIcon size={20} />
        <div className="">
          <div className="text-sm font-bold">
            {myProfile.languages && myProfile.languages.join(' | ')}
          </div>
          <div className="text-xs text-muted-foreground">Languages</div>
        </div>
      </div>
    </div>
  )
}

export default ExperienceAndLanguages
