import type { Patient } from '@/types/patient'
import {
  Button,
  Divider,
  Flex,
  Modal,
  ScrollArea,
  ScrollAreaAutosize,
  SimpleGrid,
  Space,
  Stack,
  Text
} from '@mantine/core'
import { HospitalIcon, VideoCameraIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

interface BookAppointmentProps {
  opened: boolean
  onClose: () => void
  patient: Patient
}

const BookAppointment: FC<BookAppointmentProps> = ({
  opened,
  onClose
}): ReactElement => {
  const [appointmentMode, setAppointmentMode] = useState('in-clinic')
  const [appointmentDate, setAppointmentDate] = useState('today')
  const [visitDuration, setVisitDuration] = useState('15m')
  const [appointmentTimeSlot, setAppointmentTimeSlot] = useState('')

  return (
    <Modal
      h={500}
      opened={opened}
      onClose={onClose}
      size={600}
      title={'Schedule Appointment'}
    >
      <ScrollAreaAutosize
        mah={450}
        pt={'md'}
      >
        <Stack gap={'md'}>
          <Stack gap={'md'}>
            <Text
              fw={600}
              size="sm"
            >
              Select Mode
            </Text>
            <Flex gap={'xs'}>
              <Button
                onClick={() => setAppointmentMode('in-clinic')}
                rightSection={
                  <HospitalIcon
                    size={24}
                    weight={'fill'}
                  />
                }
                variant={appointmentMode === 'in-clinic' ? 'filled' : 'default'}
              >
                In-Clinic
              </Button>
              <Button
                onClick={() => setAppointmentMode('tele-consultation')}
                rightSection={
                  <VideoCameraIcon
                    size={24}
                    weight={'fill'}
                  />
                }
                variant={
                  appointmentMode === 'tele-consultation' ? 'filled' : 'default'
                }
              >
                Tele-Consultation
              </Button>
            </Flex>
          </Stack>
          <Divider />
          <Stack gap={'md'}>
            <Text
              fw={600}
              size="sm"
            >
              Select Date
            </Text>
            <Flex gap={'xs'}>
              <Button
                onClick={() => setAppointmentDate('today')}
                variant={appointmentDate === 'today' ? 'filled' : 'default'}
              >
                Today
              </Button>
              <Button
                onClick={() => setAppointmentDate('tomorrow')}
                variant={appointmentDate === 'tomorrow' ? 'filled' : 'default'}
              >
                Tomorrow
              </Button>
            </Flex>
          </Stack>
          <Divider />
          <Stack gap={'md'}>
            <Text
              fw={600}
              size="sm"
            >
              Visit Duration
            </Text>
            <ScrollArea
              w={550}
              py={'md'}
            >
              <Flex gap={'xs'}>
                {[
                  '5m',
                  '7m',
                  '10m',
                  '15m',
                  '20m',
                  '25m',
                  '30m',
                  '45m',
                  '60m'
                ].map((val) => (
                  <Button
                    key={val}
                    onClick={() => setVisitDuration(val)}
                    variant={visitDuration === val ? 'filled' : 'default'}
                  >
                    {val}
                  </Button>
                ))}
              </Flex>
            </ScrollArea>
          </Stack>
          <Divider />
          <Stack gap={'md'}>
            <Text
              fw={600}
              size="sm"
            >
              Visit Duration
            </Text>
            {(() => {
              const mins = parseInt(visitDuration)
              if (!mins) return null
              const now = new Date()
              const start = new Date(now)
              start.setMinutes(Math.ceil(now.getMinutes() / mins) * mins, 0, 0)
              const end = new Date(now)
              end.setHours(24, 0, 0, 0)
              const slots = []
              for (
                let t = start;
                t < end;
                t = new Date(t.getTime() + mins * 60000)
              ) {
                slots.push(
                  t.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit'
                  })
                )
              }
              return (
                <SimpleGrid cols={3}>
                  {slots.map((time) => (
                    <Button
                      key={time}
                      onClick={() => setAppointmentTimeSlot(time)}
                      variant={
                        appointmentTimeSlot === time ? 'filled' : 'default'
                      }
                    >
                      {time}
                    </Button>
                  ))}
                </SimpleGrid>
              )
            })()}
          </Stack>
        </Stack>
      </ScrollAreaAutosize>
      <Space h={10} />
      <Flex
        align={'center'}
        h={40}
        justify={'center'}
      >
        <Button
          color="gray.4"
          fullWidth
          variant={'filled'}
        >
          Book slot
        </Button>
      </Flex>
    </Modal>
  )
}

export default BookAppointment
