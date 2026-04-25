import { type FC, type ReactElement } from 'react'
import { useMyProfile } from '../../hooks/use-my-profile'

const CommonlyTreats: FC = (): ReactElement => {
  const { myProfile } = useMyProfile()

  return (
    <>
      {myProfile.commonly_treats.length > 0 && (
        <div className="bg-white rounded border-gray-300 border px-4 py-4 flex items-start gap-2">
          <div className="font-bold uppercase">Specialisations</div>
          <div className="">
            {myProfile.commonly_treats.map((commonTreatment) => (
              <div
                key={commonTreatment}
                className=""
              >
                {commonTreatment}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

export default CommonlyTreats
