import { Avatar, Skeleton, Stack, Text } from '@mantine/core'
import { UserIcon } from '@phosphor-icons/react'
import { useLocation, useParams } from '@tanstack/react-router'
import { type FC, type ReactElement } from 'react'
import { useSinglePatientDetails } from '../hooks/use-patient-details'

const PatientDetailSidebarInfoCard: FC = (): ReactElement => {
  const { pathname } = useLocation()
  const { patientId } = useParams({ strict: false })
  const { data: patient } = useSinglePatientDetails(patientId)

  const isNewPatient = pathname === '/app/patient/new'
  if (isNewPatient) {
    return (
      <Stack p={'sm'}>
        <Skeleton
          h={80}
          width={'100%'}
        />
      </Stack>
    )
  }

  return (
    <div className="flex flex-col gap-1 items-center p-xl w-[300px]">
      {/* Avatar */}
      <Avatar
        radius={9999}
        size={80}
        src={null}
        alt="User avatar"
        color="blue.1"
        className="border-2 border-gray-200"
      >
        <UserIcon
          size={60}
          weight="fill"
        />
      </Avatar>

      {/* Name */}
      <Text
        style={{
          fontFamily: 'Poppins, sans-serif',
          fontWeight: 600,
          fontSize: '14px',
          lineHeight: '24px',
          color: '#002FD4',
          textAlign: 'center'
        }}
      >
        {patient?.name}
      </Text>

      {/* Age | Gender */}
      <Text
        style={{
          fontFamily: 'Poppins, sans-serif',
          fontWeight: 400,
          fontSize: '12px',
          lineHeight: '18px',
          letterSpacing: '0%',
          textTransform: 'uppercase',
          color: '#0F1011'
        }}
      >
        {patient?.age.age}Y | {patient?.gender === 'Male' ? 'M' : 'F'}
      </Text>

      {/* Diabetes Button
      {(() => {
        const fullText = "Diabetes Mellitus Type 2";
        const displayText = fullText.length <= 14 ? fullText : fullText.slice(0, 14) + '...';

        return (
          <Button
            variant="light"
            size="compact-xs"
            radius="lg"
            style={{
              width: 120,
              height: 32,
              maxWidth: '120px',
              borderRadius: 4,
              border: '1px solid #B95000',
              backgroundColor: '#FFF4EC',
              fontFamily: 'Poppins, sans-serif',
              fontWeight: 400,
              fontSize: '12px',
              lineHeight: '18px',
              letterSpacing: '0%',
              textAlign: 'center',
              color: '#B95000',
              textTransform: 'capitalize',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              cursor: 'default',
              pointerEvents: 'none',
            }}
          >
            {displayText}
          </Button>
        );
      })()} */}
    </div>
  )
}

export default PatientDetailSidebarInfoCard
