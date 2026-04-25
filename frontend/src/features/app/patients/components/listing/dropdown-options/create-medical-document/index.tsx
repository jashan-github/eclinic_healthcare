import type { Patient } from '@/types/patient'
import { Avatar, Flex, Grid, Modal, Paper, Stack, Text } from '@mantine/core'
import { PencilIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

interface CreateMedicalDocumentProps {
  opened: boolean
  onClose: () => void
  patient: Patient
}

const CreateMedicalDocument: FC<CreateMedicalDocumentProps> = ({
  opened,
  onClose
}): ReactElement => {
  return (
    <Modal
      closeOnClickOutside={false}
      opened={opened}
      onClose={onClose}
      size={'60%'}
      title={'Create medical document'}
    >
      <Grid
        gutter={40}
        py={'xl'}
      >
        <Grid.Col span={6}>
          <Stack gap={'sm'}>
            <Text
              fw={700}
              size={'sm'}
            >
              Select a medical certificate template
            </Text>
            <Grid gutter={'xs'}>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar radius={'xl'}>
                      <PencilIcon size={24} />
                    </Avatar>
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Make your own
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="L"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Leave after illness
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="F"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Fitness Adult
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="T"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Travel Certificate
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="2"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      2D ECHO
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="D"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Discharge Certificate
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="P"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Pre-Op Medical Fitness Certificate
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
            </Grid>
          </Stack>
        </Grid.Col>
        <Grid.Col span={6}>
          <Stack gap={'sm'}>
            <Text
              fw={700}
              size={'sm'}
            >
              Select a consent form template
            </Text>
            <Grid gutter={'xs'}>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar radius={'xl'}>
                      <PencilIcon size={24} />
                    </Avatar>
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Make your own
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="H"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      HIV Consent
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="P"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      PRP Consent
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="L"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Laser Hair Reduction
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
              <Grid.Col span={6}>
                <Paper
                  bg={'gray.1'}
                  className="cursor-pointer"
                  p={5}
                  withBorder
                >
                  <Flex
                    align={'center'}
                    direction={'column'}
                    gap={'sm'}
                    justify={'center'}
                  >
                    <Avatar
                      color="initials"
                      name="C"
                      radius={'xl'}
                    />
                    <Text
                      ta={'center'}
                      component="div"
                      fw={500}
                      size={'sm'}
                    >
                      Chemical peeling
                    </Text>
                  </Flex>
                </Paper>
              </Grid.Col>
            </Grid>
          </Stack>
        </Grid.Col>
      </Grid>
    </Modal>
  )
}

export default CreateMedicalDocument
