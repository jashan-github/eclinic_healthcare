import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import { Button, Card, Flex, Skeleton, Switch, Table } from '@mantine/core'
import { useForm } from '@tanstack/react-form'
import { useEffect, type FC, type ReactElement } from 'react'
import z from 'zod'
import { usePatientFields } from '../../hooks/use-patient-fields'

const patientFieldsSchema = z.array(
  z.object({
    name: z.string(),
    label: z.string(),
    selected: z.boolean()
  })
)

const LoadingRow: FC = () => (
  <Table.Tr>
    <Table.Td>
      <Skeleton h={20} />
    </Table.Td>
    <Table.Td className="flex justify-end">
      <Skeleton
        h={20}
        w={'50%'}
      />
    </Table.Td>
  </Table.Tr>
)

const PatientFields: FC = (): ReactElement => {
  const { patientFields, isLoading, isSaving, error, savePatientFields } =
    usePatientFields()

  const form = useForm({
    defaultValues: patientFields || [],
    validators: {
      onSubmit: ({ value }) => {
        const result = patientFieldsSchema.safeParse(value)
        if (!result.success) {
          return { errors: result.error.flatten().fieldErrors }
        }
        return undefined // No errors
      }
    },
    onSubmit: async ({ value }) => {
      const updatedFields = value.map(({ label, name, selected }) => ({
        label,
        name,
        selected
      }))

      savePatientFields(updatedFields)
    }
  })

  // Sync form with fetched data
  useEffect(() => {
    if (patientFields) {
      form.reset(patientFields)
    }
  }, [patientFields, form])

  if (error) {
    return <ErrorWhileFetchingData />
  }

  return (
    <Card>
      <Card.Section py={'lg'}>
        <form
          className="space-y-lg"
          onSubmit={(e) => {
            e.preventDefault()
            e.stopPropagation()
            form.handleSubmit()
          }}
        >
          <Table
            highlightOnHover
            verticalSpacing={'xs'}
            withColumnBorders
            withRowBorders
            withTableBorder
          >
            <Table.Thead>
              <Table.Tr>
                <Table.Th>FIELD</Table.Th>
                <Table.Th className="flex justify-end">ENABLE/DISABLE</Table.Th>
              </Table.Tr>
            </Table.Thead>

            <Table.Tbody>
              {isLoading ? (
                <>
                  <LoadingRow />
                  <LoadingRow />
                </>
              ) : (
                form.state.values.map((field, index) => (
                  <Table.Tr key={field.name}>
                    <Table.Td className="font-bold">{field.label}</Table.Td>
                    <Table.Td className="flex justify-end">
                      <form.Field
                        name={`[${index}].selected`}
                        children={(fieldApi) => (
                          <Switch
                            checked={fieldApi.state.value}
                            onChange={(event) =>
                              fieldApi.handleChange(event.currentTarget.checked)
                            }
                          />
                        )}
                      />
                    </Table.Td>
                  </Table.Tr>
                ))
              )}
            </Table.Tbody>
          </Table>

          <Flex justify={'flex-end'}>
            <Button
              disabled={isSaving}
              loading={isSaving}
              type={'submit'}
            >
              Save Changes
            </Button>
          </Flex>
        </form>
      </Card.Section>
    </Card>
  )
}

export default PatientFields
