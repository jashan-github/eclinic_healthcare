// visits-sidebar.tsx
import { Avatar, Card, NativeSelect } from '@mantine/core'
import { ArrowRightIcon, CalendarBlankIcon, CaretDownIcon } from '@phosphor-icons/react'
import { useEffect, useMemo, type FC } from 'react'
import type { VisitRecord } from '../../services/patient-visits-service'
import { useRxTemplates } from '../../hooks/use-patient-visits'

interface VisitsSidebarProps {
  visits: VisitRecord[]
  onVisitSelect?: (visitId: string, soapNoteId?: string) => void
  selectedClinicId: string
  onClinicChange: (clinicId: string) => void
}

const VisitsSidebar: FC<VisitsSidebarProps> = ({
  visits,
  onVisitSelect,
  selectedClinicId,
  onClinicChange,
}) => {
  const { data: rxTemplatesData, isLoading } = useRxTemplates()

  // Auto-select first clinic when templates are loaded
  useEffect(() => {
    if (rxTemplatesData?.data.templates.length && !selectedClinicId) {
      const firstClinicId = rxTemplatesData.data.templates[0].clinic_location_id
      onClinicChange(firstClinicId)
    }
  }, [rxTemplatesData?.data.templates, selectedClinicId, onClinicChange])

  // Prepare dropdown options — unique clinics from templates
  const clinicOptions = useMemo(() => {
    if (!rxTemplatesData?.data.templates) return []

    const unique = new Map<string, { id: string; name: string }>()
    rxTemplatesData.data.templates.forEach((t) => {
      if (!unique.has(t.clinic_location_id)) {
        unique.set(t.clinic_location_id, {
          id: t.clinic_location_id,
          name: t.clinic_location_name,
        })
      }
    })

    return Array.from(unique.values()).map((c) => ({
      value: c.id,
      label: c.name,
    }))
  }, [rxTemplatesData?.data.templates])

  if (!visits.length) {
    return (
      <div className="w-[500px] flex flex-col gap-sm px-2">
        <div className="min-h-[100px] flex items-center justify-center">
          <div className="flex gap-xs text-gray-800">
            <CalendarBlankIcon size={20} weight="bold" />
            <div className="font-semibold text-sm">No upcoming visits to show</div>
          </div>
        </div>
        <hr className="text-gray-200" />
      </div>
    )
  }

  // Group visits by month/year
  const groupedVisits = visits.reduce((groups, visit) => {
    const { month_name, year } = visit.appointment_date
    const key = `${month_name} ${year}`
    if (!groups[key]) groups[key] = []
    groups[key].push(visit)
    return groups
  }, {} as Record<string, VisitRecord[]>)

  return (
    <div className="w-[500px] flex flex-col gap-sm p-4">
      <div className="pb-3 border-b border-gray-200">
        <NativeSelect
          label="Clinic Location"
          data={
            isLoading
              ? [{ value: '', label: 'Loading...' }]
              : clinicOptions.length
              ? clinicOptions
              : [{ value: '', label: 'No clinics available' }]
          }
          value={selectedClinicId}
          onChange={(e) => onClinicChange(e.currentTarget.value)}
          disabled={isLoading || clinicOptions.length === 0}
          rightSection={isLoading ? null : <CaretDownIcon weight="fill" />}
          size="sm"
        />
      </div>

      {Object.entries(groupedVisits).map(([groupKey, groupVisits]) => (
        <div key={groupKey}>
          <div className="mt-md font-semibold text-gray-700">{groupKey}</div>
          {groupVisits.map((visit) => (
            <div
              key={visit.id}
              className="flex items-center gap-sm w-full flex-nowrap mt-2 cursor-pointer hover:bg-gray-50 rounded"
              onClick={() => onVisitSelect?.(visit.id, visit.soap_note?.id)}
            >
              <div className="flex flex-col gap-0">
                <span className="font-semibold text-lg">{visit.appointment_date.day}</span>
                <span className="text-xs">{visit.appointment_date.day_name}</span>
              </div>
              <Card className="cursor-pointer" p={8} radius="xl" shadow="sm" w="100%" withBorder>
                <div className="flex items-center gap-sm">
                  <Avatar color="pink.6" radius="xl" size={28}>Rx</Avatar>
                  <div className="text-gray-700 font-bold text-sm">
                    Visit on {visit.appointment_date.day}th {visit.appointment_date.month_name},{' '}
                    {visit.appointment_date.year} at {visit.appointment_start_time.slice(0, 5)}
                  </div>
                  <ArrowRightIcon />
                </div>
              </Card>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}

export default VisitsSidebar