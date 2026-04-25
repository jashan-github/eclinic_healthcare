import type { Patient } from '@/types/patient'
import {
  Button,
  Drawer,
  Flex,
  Grid,
  ScrollArea,
  Stack,
  Text
} from '@mantine/core'
import { ArrowLeftIcon, QuestionIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import AvailableLabTestsAndPackages from './available-lab-tests-and-packages.tsx'
import LabTestCustomerDetails from './lab-test-customer-details.tsx'
import LabTestDiscountInformation from './lab-test-discount-information.tsx'
import LabTestPatientAddress from './lab-test-patient-address.tsx'
import LabTestRecipientContact from './lab-test-recipient-contact.tsx'
import LabTestSearchLabTestsAndRadiology from './lab-test-search-lab-tests-and-radiology.tsx'
import SelectedLabTests from './lab-test-selected-lab-tests.tsx'
import LabTestTotalAmountToBePaid from './lab-test-total-amount-to-be-paid.tsx.tsx'

interface BookLabTestProps {
  opened: boolean
  onClose: () => void
  patient: Patient
}

const BookLabTest: FC<BookLabTestProps> = ({
  opened,
  onClose
}): ReactElement => {
  return (
    <Drawer
      closeOnClickOutside={false}
      opened={opened}
      onClose={onClose}
      position={'right'}
      size={'80%'}
      styles={{
        body: {
          padding: 0
        }
      }}
      withCloseButton={false}
    >
      <Stack
        gap={0}
        h={'100vh'}
      >
        {/* Custom Header Wrapper */}
        <Flex
          align={'center'}
          className="shadow-sm"
          h={60}
          justify={'space-between'}
          px={'md'}
        >
          <Flex
            align={'center'}
            className="cursor-pointer"
            gap={'sm'}
            justify={'flex-end'}
            onClick={onClose}
          >
            <ArrowLeftIcon />
            <Text fw={700}>Book Lab Test</Text>
            <Text size={'xs'}>for Ricky | 22y | M</Text>
          </Flex>
          <Button
            leftSection={<QuestionIcon />}
            variant={'outline'}
          >
            Need Help?
          </Button>
        </Flex>
        <ScrollArea
          bg={'gray.1'}
          h={'calc(100vh - 60px)'}
          p={'md'}
          scrollbars="y"
        >
          <Stack gap={'sm'}>
            <LabTestSearchLabTestsAndRadiology />
            <Grid gutter={'sm'}>
              <Grid.Col span={8}>
                <Stack gap={'sm'}>
                  <SelectedLabTests />

                  <AvailableLabTestsAndPackages />
                </Stack>
              </Grid.Col>
              <Grid.Col span={4}>
                <Stack gap={'sm'}>
                  <LabTestDiscountInformation />
                  <LabTestTotalAmountToBePaid />
                  <LabTestPatientAddress />
                  <LabTestRecipientContact />
                  <LabTestCustomerDetails />
                </Stack>
              </Grid.Col>
            </Grid>
          </Stack>
        </ScrollArea>
      </Stack>
    </Drawer>
  )
}

export default BookLabTest
