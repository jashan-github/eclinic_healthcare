import { type FC, type ReactElement } from 'react'
import { useMyProfile } from '../../hooks/use-my-profile'

const AwardsAndPublications: FC = (): ReactElement => {
  const { myProfile } = useMyProfile()

  return (
    <>
      {myProfile.specializations.length > 0 && (
        <div className="bg-white rounded border-gray-300 border px-4 py-4 flex items-start gap-2">
          <div className="font-bold uppercase">Awards & Publications</div>
          <div className="">
            {myProfile.specializations.map((specialisation) => (
              <div
                key={specialisation}
                className=""
              >
                {specialisation}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

export default AwardsAndPublications
