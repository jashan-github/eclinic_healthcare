import { Table } from '@mantine/core'
import { type FC, type ReactElement, useMemo } from 'react'
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef
} from '@tanstack/react-table'
import { usePatientReferrals } from '../hooks/use-patient-referrals'
import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import type { PatientReferral } from '@/types/patient-referral'

const PatientReferralTable: FC = (): ReactElement => {
  const { patientReferrals, isLoading, error } = usePatientReferrals()

  const columns = useMemo<ColumnDef<PatientReferral>[]>(
    () => [
      { accessorKey: 'id', header: 'S.No.' },
      { accessorKey: 'doctor_name', header: 'Healthcare Provider Name' },
      { accessorKey: 'contact_number', header: 'Contact Number' },
      { accessorKey: 'referrals_received', header: 'Referrals Received' },
      { accessorKey: 'referrals_given', header: 'Referrals Given' }
    ],
    []
  )

  const patientReferralsTable = useReactTable({
    data: patientReferrals,
    columns,
    getCoreRowModel: getCoreRowModel()
  })

  if (isLoading) {
    return (
      <div className="flex h-screen overflow-hidden justify-center items-center w-full">
        <GlobalLoader />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen overflow-hidden justify-center items-center w-full">
        <ErrorWhileFetchingData />
      </div>
    )
  }

  return (
    <Table>
      <Table.Thead className="bg-gray-300">
        {patientReferralsTable.getHeaderGroups().map((headerGroup) => (
          <Table.Tr key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <Table.Th key={header.id}>
                {flexRender(
                  header.column.columnDef.header,
                  header.getContext()
                )}
              </Table.Th>
            ))}
          </Table.Tr>
        ))}
      </Table.Thead>
      <Table.Tbody>
        {patientReferralsTable.getRowModel().rows.map((row) => (
          <Table.Tr key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <Table.Td key={cell.id}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </Table.Td>
            ))}
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

export default PatientReferralTable
