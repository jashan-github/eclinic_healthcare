import type { Patient } from '@/types/patient'
import {
  Avatar,
  Button,
  Divider,
  Flex,
  Grid,
  Modal,
  Paper,
  ScrollArea,
  Select,
  Stack,
  Text
} from '@mantine/core'
import { DatePickerInput } from '@mantine/dates'
import {
  CalendarBlankIcon,
  FilePdfIcon,
  FilesIcon,
  FloppyDiskIcon,
  TrashSimpleIcon
} from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import ReportTagsInput from './report-tags-input'

interface AddMedicalRecordsProps {
  opened: boolean
  onClose: () => void
  patient: Patient
}

const AddMedicalRecords: FC<AddMedicalRecordsProps> = ({
  opened,
  onClose
}): ReactElement => {
  return (
    <Modal
      closeOnClickOutside={false}
      opened={opened}
      onClose={onClose}
      size={'xl'}
      title={'Upload a medical record'}
    >
      <Stack
        h={500}
        pt={'md'}
      >
        <ScrollArea h={450}>
          <Paper
            bg={'gray.1'}
            py={'sm'}
            radius={'lg'}
          >
            <Stack gap={'sm'}>
              {/* Report Header */}
              <Flex
                align={'center'}
                justify={'space-between'}
                px={'sm'}
              >
                <Text size="xs">sample-pdf.pdf</Text>
                <Button
                  color="red"
                  leftSection={<TrashSimpleIcon />}
                  variant={'transparent'}
                >
                  Delete File
                </Button>
              </Flex>
              <Divider />
              <Grid px={'sm'}>
                <Grid.Col span={2}>
                  <Avatar
                    className="cursor-pointer"
                    size={80}
                    radius={'sm'}
                  >
                    <FilePdfIcon
                      color="red"
                      size={50}
                    />
                  </Avatar>
                </Grid.Col>
                <Grid.Col span={3}>
                  <Select
                    label="Report Type"
                    placeholder="Select file type"
                    data={[
                      'Prescription',
                      'Lab Report',
                      'Scan',
                      'Other',
                      'Discharge Summary',
                      'Vaccine Certificate',
                      'Insurance',
                      'Invoice'
                    ]}
                  />
                </Grid.Col>
                <Grid.Col span={3}>
                  <DatePickerInput
                    leftSection={<CalendarBlankIcon size={18} />}
                    leftSectionPointerEvents="none"
                    label="Investigation Date"
                    placeholder="dd/mm/yyyy"
                  />
                </Grid.Col>
                <Grid.Col span={4}>
                  <ReportTagsInput />
                </Grid.Col>
              </Grid>
            </Stack>
          </Paper>
        </ScrollArea>
        <Flex
          h={50}
          align={'center'}
          justify={'space-between'}
        >
          <Button
            leftSection={<FilesIcon />}
            variant={'outline'}
          >
            Upload record
          </Button>
          <Button leftSection={<FloppyDiskIcon />}>Save</Button>
        </Flex>
      </Stack>
    </Modal>
  )
}

export default AddMedicalRecords
