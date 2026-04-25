import { Box, Button, Flex, Image, Text } from '@mantine/core'
import { Link } from '@tanstack/react-router'
import { type FC, type ReactElement } from 'react'

interface ErrorWhileFetchingDataProps {
  width?: number
}

const ErrorWhileFetchingData: FC<ErrorWhileFetchingDataProps> = ({
  width = 200
}): ReactElement => {
  return (
    <Flex
      gap={5}
      justify={'center'}
      align={'center'}
      direction={'column'}
      className="h-full overflow-hidden w-full"
    >
      <Box w={width}>
        <Image
          src="/assets/icons/error-loading-data.svg"
          alt="Error loading data"
          width={width}
          height={'auto'}
        />
      </Box>
      <Text fw={600}>Error Loading Data</Text>
      <Button variant={'filled'}>
        <Link to={'/'}>Go to Home</Link>
      </Button>
    </Flex>
  )
}

export default ErrorWhileFetchingData
