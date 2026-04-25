import {
  Avatar,
  Button,
  Divider,
  Flex,
  Group,
  Image,
  Paper,
  Stack,
  Text,
  Title
} from '@mantine/core'
import { TestTubeIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
// import LabTestPreferredLabPartnerOptions from './lab-test-preferred-lab-partner-options'

const AvailableLabTestsAndPackages: FC = (): ReactElement => {
  return (
    <Paper>
      <Stack p={'sm'}>
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'flex-start'}
        >
          <Avatar
            bg={'green'}
            color="#fff"
            radius={'sm'}
            size={'sm'}
          >
            <TestTubeIcon
              size={20}
              weight={'fill'}
            />
          </Avatar>
          <Title order={6}>Available Options (5)</Title>
        </Flex>
      </Stack>
      <Divider />
      <Stack
        gap={'sm'}
        p={'sm'}
      >
        {/* Disable it for now.  */}
        {/* <LabTestPreferredLabPartnerOptions /> */}
        <Paper
          p={'md'}
          withBorder
        >
          <Stack gap={'sm'}>
            <Flex
              align={'center'}
              justify={'space-between'}
            >
              <Text fw={600}>Option 1</Text>
              <Text fw={600}>&#8377; 1394.00</Text>
            </Flex>
            <Stack gap={'xs'}>
              <Text
                component="span"
                size={'sm'}
              >
                <Text
                  c={'gray.8'}
                  component="span"
                  fw={600}
                  mr={'md'}
                >
                  1. CBC Hemogram:
                </Text>
                &#8377;310.00
              </Text>
              <Text
                component="span"
                size={'sm'}
              >
                <Text
                  c={'gray.8'}
                  component="span"
                  fw={600}
                  mr={'md'}
                >
                  Home Collection Fees:
                </Text>
                &#8377;150.00
              </Text>
              <Flex
                align={'center'}
                justify={'space-between'}
              >
                <Group gap={'sm'}>
                  <Text
                    fw={600}
                    size={'sm'}
                  >
                    Provided By
                  </Text>
                  <Image
                    radius="md"
                    src="https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/images/bg-7.png"
                    w={50}
                  />
                </Group>
                <Button variant={'outline'}>Select Package</Button>
              </Flex>
            </Stack>
          </Stack>
        </Paper>
        <Paper
          p={'md'}
          withBorder
        >
          <Stack gap={'sm'}>
            <Flex
              align={'center'}
              justify={'space-between'}
            >
              <Text fw={600}>Option 1</Text>
              <Text fw={600}>&#8377; 1394.00</Text>
            </Flex>
            <Stack gap={'xs'}>
              <Text
                component="span"
                size={'sm'}
              >
                <Text
                  c={'gray.8'}
                  component="span"
                  fw={600}
                  mr={'md'}
                >
                  1. CBC Hemogram:
                </Text>
                &#8377;310.00
              </Text>
              <Text
                component="span"
                size={'sm'}
              >
                <Text
                  c={'gray.8'}
                  component="span"
                  fw={600}
                  mr={'md'}
                >
                  Home Collection Fees:
                </Text>
                &#8377;150.00
              </Text>
              <Flex
                align={'center'}
                justify={'space-between'}
              >
                <Group gap={'sm'}>
                  <Text
                    fw={600}
                    size={'sm'}
                  >
                    Provided By
                  </Text>
                  <Image
                    radius="md"
                    src="https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/images/bg-7.png"
                    w={50}
                  />
                </Group>
                <Button variant={'outline'}>Select Package</Button>
              </Flex>
            </Stack>
          </Stack>
        </Paper>
        <Paper
          p={'md'}
          withBorder
        >
          <Stack gap={'sm'}>
            <Flex
              align={'center'}
              justify={'space-between'}
            >
              <Text fw={600}>Option 1</Text>
              <Text fw={600}>&#8377; 1394.00</Text>
            </Flex>
            <Stack gap={'xs'}>
              <Text
                component="span"
                size={'sm'}
              >
                <Text
                  c={'gray.8'}
                  component="span"
                  fw={600}
                  mr={'md'}
                >
                  1. CBC Hemogram:
                </Text>
                &#8377;310.00
              </Text>
              <Text
                component="span"
                size={'sm'}
              >
                <Text
                  c={'gray.8'}
                  component="span"
                  fw={600}
                  mr={'md'}
                >
                  Home Collection Fees:
                </Text>
                &#8377;150.00
              </Text>
              <Flex
                align={'center'}
                justify={'space-between'}
              >
                <Group gap={'sm'}>
                  <Text
                    fw={600}
                    size={'sm'}
                  >
                    Provided By
                  </Text>
                  <Image
                    radius="md"
                    src="https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/images/bg-7.png"
                    w={50}
                  />
                </Group>
                <Button variant={'outline'}>Select Package</Button>
              </Flex>
            </Stack>
          </Stack>
        </Paper>
      </Stack>
    </Paper>
  )
}

export default AvailableLabTestsAndPackages
