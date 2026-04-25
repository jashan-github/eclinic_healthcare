import { Text, List, ThemeIcon } from '@mantine/core';
import { StethoscopeIcon } from '@phosphor-icons/react';
import { useMyProfile } from '../../hooks/use-my-profile';

export default function SpecializationsList() {
  const { myProfile } = useMyProfile();
  const specializations = myProfile?.specializations || [];

  return (
    <div className="min-h-[128px] p-[17px] pl-[30px] rounded-[16px] border border-[#D6D9E0] bg-white">
      <Text fw={700} mb={10} className="font-poppins font-bold text-[14.5px] leading-[22px] capitalize text-[#0F1011]">
        Specialisations
      </Text>
      <List spacing="xs" className="mt-2">
        {specializations.length === 0 ? (
          ['Urologist', 'Vascular Surgeon'].map((spec, i) => (
            <List.Item
              key={i}
              icon={
                <ThemeIcon color="white" size={20} radius="xl">
                  <StethoscopeIcon size={14} weight="bold" color="black" />
                </ThemeIcon>
              }
            >
              <Text fw={600} className="font-poppins font-semibold text-[12.91px] leading-[20px] capitalize text-[#0F1011]">
                {spec}
              </Text>
            </List.Item>
          ))
        ) : (
          specializations.map((spec: any) => (
            <List.Item
              key={spec.id}
              icon={
                <ThemeIcon color="white" size={20} radius="xl">
                  <StethoscopeIcon size={14} weight="bold" color="black" />
                </ThemeIcon>
              }
            >
              <Text fw={600} className="font-poppins font-semibold text-[12.91px] leading-[20px] capitalize text-[#0F1011]">
                {spec.name}   {/* ← YEH FIX HAI */}
              </Text>
            </List.Item>
          ))
        )}
      </List>
    </div>
  );
}