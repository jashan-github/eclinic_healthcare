import type { Patient } from '@/types/patient'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  ActionIcon,
  Button,
  Divider,
  Flex,
  Grid,
  Modal,
  NumberInput,
  Select,
  Stack,
  Table,
  Text,
  Textarea,
  TextInput
} from '@mantine/core'
import {
  PaperPlaneRightIcon,
  PlusIcon,
  TrashSimpleIcon
} from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { Controller, useFieldArray, useForm } from 'react-hook-form'
import z from 'zod'

interface CreateReceiptProps {
  opened: boolean
  onClose: () => void
  patient: Patient | null
}

const receiptSchema = z.object({
  name: z.string(),
  uhid: z.string(),
  phone_number: z.string().length(10),
  services: z
    .object({
      name: z.string(),
      quantity: z.number().min(1),
      amount: z.number(),
      discount: z.number(),
      total: z.number()
    })
    .array(),
  additional_discount: z.number(),
  payment_mode: z
    .object({
      mode: z.string(),
      amount: z.number()
    })
    .array(),
  payment_id: z.string(),
  remarks: z.string()
})

type FormData = z.infer<typeof receiptSchema>

const CreateReceipt: FC<CreateReceiptProps> = ({
  opened,
  onClose
}): ReactElement => {
  const { control, handleSubmit, setValue, watch } = useForm<FormData>({
    defaultValues: {
      services: [{ name: '', quantity: 1, amount: 0, discount: 0, total: 0 }],
      payment_mode: [
        {
          mode: 'Cash',
          amount: 0
        }
      ]
    },
    resolver: zodResolver(receiptSchema)
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'services'
  })

  const {
    fields: paymentModeFields,
    append: appendPaymentMode,
    remove: removePaymentMode
  } = useFieldArray({
    control,
    name: 'payment_mode'
  })

  // Auto-calculate total per row
  const services = watch('services')
  services?.forEach((s, i) => {
    const total = s.amount * s.quantity - s.discount
    if (total !== s.total) {
      setValue(`services.${i}.total`, total)
    }
  })

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size={'xl'}
      title={'Create Receipt'}
    >
      <form onSubmit={handleSubmit(console.log)}>
        <Stack gap={'md'}>
          <Grid>
            <Grid.Col span={3}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextInput
                    label="Name"
                    withAsterisk
                    {...field}
                  />
                )}
              />
            </Grid.Col>
            <Grid.Col span={3}>
              <Controller
                name="uhid"
                control={control}
                render={({ field }) => (
                  <TextInput
                    disabled
                    label="UHID"
                    {...field}
                  />
                )}
              />
            </Grid.Col>
            <Grid.Col span={3}>
              <Controller
                name="phone_number"
                control={control}
                render={({ field }) => (
                  <NumberInput
                    hideControls
                    label="Phone"
                    leftSection={<>+91</>}
                    maxLength={10}
                    minLength={10}
                    {...field}
                  />
                )}
              />
            </Grid.Col>
            <Grid.Col span={3}>
              <TextInput
                label="Payment Status"
                disabled
                value={'Unbilled'}
              />
            </Grid.Col>
          </Grid>
          <Table
            withColumnBorders
            withRowBorders
            withTableBorder
          >
            <Table.Thead bg={'gray.1'}>
              <Table.Tr>
                <Table.Th>SERVICE</Table.Th>
                <Table.Th>QTY</Table.Th>
                <Table.Th>AMOUNT</Table.Th>
                <Table.Th>DISCOUNT</Table.Th>
                <Table.Th>TOTAL</Table.Th>
                <Table.Th></Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {fields.map((field, index) => (
                <Table.Tr key={field.id}>
                  <Table.Td>
                    <Controller
                      name={`services.${index}.name`}
                      control={control}
                      render={({ field }) => <TextInput {...field} />}
                    />
                  </Table.Td>
                  <Table.Td>
                    <Controller
                      name={`services.${index}.quantity`}
                      control={control}
                      render={({ field }) => (
                        <NumberInput
                          hideControls
                          min={1}
                          {...field}
                        />
                      )}
                    />
                  </Table.Td>
                  <Table.Td>
                    <Controller
                      name={`services.${index}.amount`}
                      control={control}
                      render={({ field }) => (
                        <NumberInput
                          hideControls
                          min={0}
                          {...field}
                        />
                      )}
                    />
                  </Table.Td>
                  <Table.Td>
                    <Controller
                      name={`services.${index}.discount`}
                      control={control}
                      render={({ field }) => (
                        <NumberInput
                          hideControls
                          min={0}
                          {...field}
                        />
                      )}
                    />
                  </Table.Td>
                  <Table.Td>
                    <Controller
                      name={`services.${index}.total`}
                      control={control}
                      render={({ field }) => <TextInput {...field} />}
                    />
                  </Table.Td>
                  <Table.Td>
                    <ActionIcon
                      color="gray.5"
                      onClick={() => remove(index)}
                      variant={'transparent'}
                    >
                      <TrashSimpleIcon
                        size={16}
                        weight={'fill'}
                      />
                    </ActionIcon>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
          <Flex>
            <Button
              leftSection={<PlusIcon />}
              onClick={() =>
                append({
                  name: '',
                  quantity: 1,
                  amount: 0,
                  discount: 0,
                  total: 0
                })
              }
              variant={'transparent'}
              w={'max-fit'}
            >
              Add another
            </Button>
          </Flex>

          <Flex justify={'space-between'}>
            <Stack>
              <Controller
                name="additional_discount"
                control={control}
                render={({ field }) => (
                  <TextInput
                    label="Additional Discount"
                    {...field}
                  />
                )}
              />

              {/* Payment mode fields */}
              {paymentModeFields.map((field, index) => (
                <Flex
                  align="flex-end"
                  gap="md"
                  key={field.id}
                >
                  <Controller
                    name={`payment_mode.${index}.mode`}
                    control={control}
                    render={({ field }) => (
                      <Select
                        label={index === 0 ? 'Pay mode' : ' '}
                        data={[
                          'Cash',
                          'Credit Card',
                          'Debit Card',
                          'Paytm',
                          'GPay',
                          'UPI',
                          'Other'
                        ]}
                        {...field}
                      />
                    )}
                  />
                  <Controller
                    name={`payment_mode.${index}.amount`}
                    control={control}
                    render={({ field }) => (
                      <NumberInput
                        hideControls
                        label=" "
                        min={0}
                        {...field}
                      />
                    )}
                  />
                  {index === 1 && (
                    <ActionIcon
                      size="lg"
                      variant="transparent"
                      onClick={() => removePaymentMode(index)}
                    >
                      <TrashSimpleIcon />
                    </ActionIcon>
                  )}
                  {paymentModeFields.length === 1 && (
                    <ActionIcon
                      size="lg"
                      variant="transparent"
                      onClick={() =>
                        appendPaymentMode({ mode: 'Cash', amount: 0 })
                      }
                    >
                      <PlusIcon />
                    </ActionIcon>
                  )}
                </Flex>
              ))}

              <Controller
                name="payment_id"
                control={control}
                render={({ field }) => (
                  <TextInput
                    label="Payment ID (Optional)"
                    {...field}
                  />
                )}
              />
            </Stack>
            <Stack gap={2}>
              <Flex
                gap={'xl'}
                justify={'space-between'}
              >
                <Text
                  fw={700}
                  size={'sm'}
                >
                  Total Amount:
                </Text>
                <Text
                  c={'green.6'}
                  size={'sm'}
                >
                  &#8377; 100
                </Text>
              </Flex>
              <Flex
                gap={'xl'}
                justify={'space-between'}
              >
                <Text
                  fw={700}
                  size={'sm'}
                >
                  Line item discount:
                </Text>
                <Text
                  c={'green.6'}
                  size={'sm'}
                >
                  -&#8377; 100
                </Text>
              </Flex>
              <Flex
                gap={'xl'}
                justify={'space-between'}
              >
                <Text
                  fw={700}
                  size={'sm'}
                >
                  Additional Discount:
                </Text>
                <Text
                  c={'green.6'}
                  size={'sm'}
                >
                  -&#8377; 400
                </Text>
              </Flex>
              <Flex
                gap={'xl'}
                justify={'space-between'}
              >
                <Text
                  fw={700}
                  size={'sm'}
                >
                  Grand Total:
                </Text>
                <Text
                  c={'green.6'}
                  size={'sm'}
                >
                  &#8377; 200
                </Text>
              </Flex>

              <Divider />
              <Flex
                gap={'xl'}
                justify={'space-between'}
              >
                <Text
                  fw={700}
                  size={'sm'}
                >
                  Amount Paid:
                </Text>
                <Text
                  c={'green.6'}
                  size={'sm'}
                >
                  &#8377; 200
                </Text>
              </Flex>
            </Stack>
          </Flex>
          <Controller
            name="remarks"
            control={control}
            render={({ field }) => (
              <Textarea
                label="Remarks"
                {...field}
              />
            )}
          />
          <Flex justify={'flex-end'}>
            <Button
              leftSection={<PaperPlaneRightIcon />}
              type="submit"
            >
              Create
            </Button>
          </Flex>
        </Stack>
      </form>
    </Modal>
  )
}

export default CreateReceipt
