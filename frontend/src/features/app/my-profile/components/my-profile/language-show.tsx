
import { GlobeIcon } from '@phosphor-icons/react';
import { Text } from '@mantine/core';
import { useMyProfile } from '../../hooks/use-my-profile';

export default function LanguagesShow() {
  const { myProfile } = useMyProfile()
  console.log("myProfile.languages.length", myProfile.languages)
  return (
    <div className="min-h-[78px] bg-white border border-[#D6D9E0] rounded-[16px] px-[30px] py-[5px] flex items-center gap-4">
      <GlobeIcon size={20} className="text-gray-600 flex-shrink-0" />

      <div className="flex flex-col gap-1">
        <Text fw={700} size="sm" className="font-poppins text-[14.5px] leading-[20px] capitalize text-[#0F1011]">
          Languages
        </Text>

        <Text fw={300} className='font-poppins leading-[24px] capitalize text-[#0F1011]'>
          {myProfile.languages?.length > 0
            ? myProfile.languages.map((lang: any) => lang.language_name).join(' | ')
            : ''
          }
        </Text>
      </div>
    </div>
  );
}
