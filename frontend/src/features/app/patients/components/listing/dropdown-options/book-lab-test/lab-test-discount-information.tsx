import {
  Avatar,
  Button,
  Divider,
  Flex,
  NumberInput,
  Paper,
  Stack,
  Text,
  Title
} from '@mantine/core'
import { TagIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

const LabTestDiscountInformation: FC = (): ReactElement => {
  return (
    <Paper>
      <Stack p={'sm'}>
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'flex-start'}
        >
          <Avatar
            bg={'#a624a0'}
            color="#fff"
            radius={'sm'}
            size={'sm'}
          >
            <TagIcon
              size={20}
              weight={'fill'}
            />
          </Avatar>
          <Title order={6}>Discount</Title>
        </Flex>
      </Stack>
      <Divider />
      <Stack
        gap={'sm'}
        p={'sm'}
      >
        <Text>Enter discount percentage</Text>
        <Flex gap={'sm'}>
          <NumberInput
            rightSection={<>%</>}
            placeholder="000"
          />
          <Button>Apply</Button>
        </Flex>
        <Text
          c={'gray.6'}
          fw={500}
          size={'sm'}
        >
          30% maximum discount applicable
        </Text>
      </Stack>
    </Paper>
  )
}

export default LabTestDiscountInformation
