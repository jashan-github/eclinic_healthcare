import {
  Box,
  Card,
  ColorSwatch,
  Divider,
  Flex,
  ScrollArea,
  Stack,
  Text,
  Timeline
} from '@mantine/core'
import { type FC, type ReactElement } from 'react'

const PatientTreatments: FC = (): ReactElement => {
  return (
    <Stack
      h={'100vh'}
      gap={0}
    >
      <Box
        h={60}
        bg={'white'}
        px={'sm'}
        w={'100%'}
      >
        <Flex
          h={60}
          w={'100%'}
          align={'center'}
          justify={'space-between'}
        >
          <Text
            component="div"
            fw={500}
          >
            Treatments
          </Text>
        </Flex>
      </Box>
      <Divider />
      <Box
        bg={'white'}
        h={50}
        w={'100%'}
      >
        <Flex
          align={'center'}
          gap={'sm'}
          h={50}
          px={'md'}
          w={'100%'}
        >
          <ColorSwatch
            color="green"
            size={16}
          />
          <Text
            component="div"
            fw={600}
            size={'lg'}
          >
            Demo
          </Text>
          <Text
            component="div"
            size={'14'}
          >
            0/2 Sessions completed
          </Text>
        </Flex>
      </Box>
      <ScrollArea h={'100vh-120px'}>
        <Box p={'lg'}>
          <Timeline
            px={'md'}
            active={0}
            bulletSize={36}
            lineWidth={2}
          >
            <Timeline.Item
              bullet={1}
              title=""
            >
              <Card
                px={'sm'}
                py={'xs'}
                radius={'md'}
                bg={'white'}
              >
                <Flex
                  align={'center'}
                  gap={'sm'}
                >
                  <Text size="sm">Session 1</Text>
                  <Divider
                    color="gray.3"
                    orientation={'vertical'}
                  />
                </Flex>
              </Card>
            </Timeline.Item>

            <Timeline.Item
              bullet={2}
              title=""
            >
              <Card
                px={'sm'}
                py={'xs'}
                radius={'md'}
                bg={'white'}
              >
                <Flex
                  align={'center'}
                  gap={'sm'}
                >
                  <Text size="sm">Session 2</Text>
                  <Divider
                    color="gray.3"
                    orientation={'vertical'}
                  />
                </Flex>
              </Card>
            </Timeline.Item>
          </Timeline>
        </Box>
      </ScrollArea>
    </Stack>
  )
}

export default PatientTreatments
