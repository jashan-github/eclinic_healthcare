import { type FC, type ReactElement } from 'react'
import { useMyProfile } from '../../hooks/use-my-profile'

const HeroSection: FC = (): ReactElement => {
  const { myProfile } = useMyProfile()
  console.log("Image URL",myProfile.profile_img_url)
  return (
    <div className="">
      <div className="flex gap-5">
        {myProfile?.profile_img_url && (
          <img
            src={myProfile?.profile_img_url}
            alt="Profile"
            className="w-[150px] h-[150px] object-cover rounded-full border-1 bg-[#E8EEFD] border-[#E8EEFD]"
          />
        )}
        <div className="flex flex-col gap-2">
          <div className="font-poppins font-semibold text-[31px] leading-[36px] align-middle">{`Dr. ${myProfile?.first_name} ${myProfile?.middle_name} ${myProfile?.last_name}`}</div>
          <div className="font-poppins font-semibold text-[15px] leading-[20px] align-middle">{ myProfile?.major_specialization || 'Healthcare Provider' }</div>
          <div className="font-poppins font-light text-[15px] leading-[20px] text-[#002FD4] align-middle">{myProfile.years_of_experience || '0'} years of experience</div>
        </div>
      </div>
    </div>
  )
}

export default HeroSection
