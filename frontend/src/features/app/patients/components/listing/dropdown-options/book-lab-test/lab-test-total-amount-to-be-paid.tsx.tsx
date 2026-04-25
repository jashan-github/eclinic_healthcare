import { Avatar, Divider, Flex, Paper, Stack, Text, Title } from '@mantine/core'
import { type FC, type ReactElement } from 'react'

const LabTestTotalAmountToBePaid: FC = (): ReactElement => {
  return (
    <Paper>
      <Stack p={'sm'}>
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'flex-start'}
        >
          <Avatar
            bg="#004ba8"
            color="#ffffff"
            radius={'sm'}
            size={'sm'}
          >
            XCG
          </Avatar>
          <Title order={6}>Amount to be paid</Title>
        </Flex>
      </Stack>
      <Divider />
      <Stack
        gap={'sm'}
        p={'sm'}
      >
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'space-between'}
        >
          <Text size={'sm'}>Total MRP</Text>
          <Text size={'sm'}>&#8377; 249.00</Text>
        </Flex>
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'space-between'}
        >
          <Text size={'sm'}>Discount</Text>
          <Text
            c={'green.8'}
            size={'sm'}
          >
            -0%
          </Text>
        </Flex>
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'space-between'}
        >
          <Text size={'sm'}>Discounted Price</Text>
          <Text size={'sm'}>&#8377; 249.00</Text>
        </Flex>
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'space-between'}
        >
          <Text size={'sm'}>Home collection fees</Text>
          <Text size={'sm'}>&#8377; 150.00</Text>
        </Flex>
        <Divider />
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'space-between'}
        >
          <Text
            fw={600}
            size={'md'}
          >
            Total
          </Text>
          <Text
            fw={600}
            size={'md'}
          >
            &#8377; 399.00
          </Text>
        </Flex>
      </Stack>
    </Paper>
  )
}

export default LabTestTotalAmountToBePaid
