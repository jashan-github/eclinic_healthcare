import { Text } from '@mantine/core';
import { useMyProfile } from '../../hooks/use-my-profile';

export default function DoctorIntro() {
  const { myProfile } = useMyProfile()

  return (
    <div className="min-h-[148px] p-[17px] pl-[30px] rounded-[16px] border border-[#D6D9E0] bg-white">
      <Text fw={700} mb={10} className="font-poppins font-bold text-[14.5px] leading-[22px] capitalize text-[#0F1011]">
        Intro
      </Text>
      <Text pl={10}>
        {myProfile.intro}
      </Text>
    </div>
  );
}