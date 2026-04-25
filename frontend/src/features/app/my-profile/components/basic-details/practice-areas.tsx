import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { useMedicalPracticeAreas } from '@/hooks/use-medical-practice-areas'
import type { PracticeAreaCompact } from '@/types/practice-area'
import { Autocomplete, Badge, Button } from '@mantine/core'
import { XIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'
import { usePracticeAreas } from '../../hooks/use-practice-areas'

const PracticeAreas: FC = (): ReactElement => {
  const [searchQuery, setSearchQuery] = useState('')
  const [tempPracticeAreas, setTempPracticeAreas] = useState<
    PracticeAreaCompact[]
  >([])

  const {
    medicalPracticeAreas,
    isLoading: isLoadingMedicalPracticeAreas,
    error: medicalPracticeAreasError
  } = useMedicalPracticeAreas(searchQuery)
  const {
    practiceAreas,
    isLoading: isLoadingPracticeAreas,
    isDeleting,
    isSaving,
    savePracticeArea
  } = usePracticeAreas()

  const handleSelect = (selectedArea: PracticeAreaCompact) => {
    setTempPracticeAreas([...tempPracticeAreas, selectedArea])
    setSearchQuery('')
  }

  const handleRemove = (id: string) => {
    setTempPracticeAreas(tempPracticeAreas.filter((area) => area.id !== id))
  }

  const handleSave = () => {
    savePracticeArea([...(practiceAreas || []), ...tempPracticeAreas])
    setTempPracticeAreas([])
  }

  if (isLoadingPracticeAreas || isDeleting) return <GlobalLoader />
  if (medicalPracticeAreasError) return <ErrorWhileFetchingData />

  console.log(isLoadingMedicalPracticeAreas)

  const filteredPracticeAreas =
    medicalPracticeAreas
      ?.filter(
        (area) =>
          !(practiceAreas || []).some((existing) => existing.id === area.id) &&
          !tempPracticeAreas.some((existing) => existing.id === area.id)
      )
      ?.map((area) => ({ value: area.name, label: area.name, ...area })) || []

  return (
    <div className="flex flex-col gap-4 py-4">
      {/* Autocomplete Input */}
      <Autocomplete
        placeholder="Search medical practice areas..."
        value={searchQuery}
        onChange={setSearchQuery}
        data={filteredPracticeAreas}
        onOptionSubmit={(value) => {
          const selected = filteredPracticeAreas.find(
            (area) => area.value === value
          )
          if (selected) handleSelect(selected)
        }}
        classNames={{ input: 'border border-gray-300 rounded' }}
      />

      {/* Areas currently practicing */}
      <div className="flex flex-wrap gap-2">
        {practiceAreas?.map((v) => (
          <Badge
            key={v.id}
            color="gray"
            radius="sm"
            styles={{
              root: {
                padding: '0 8px',
                height: '40px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                border: '1px solid #e5e7eb'
              }
            }}
            variant="filled"
          >
            <span className="first-letter:uppercase">{v.name}</span>
            {practiceAreas.length >= 2 && (
              <Button
                variant="subtle"
                size="xs"
                styles={{ root: { padding: 0, width: '24px', height: '24px' } }}
              >
                <XIcon size={16} />
              </Button>
            )}
          </Badge>
        ))}

        {/* Newly added practice areas */}
        {tempPracticeAreas.map((v) => (
          <Badge
            key={v.id}
            color="gray"
            radius="sm"
            styles={{
              root: {
                padding: '0 8px',
                height: '40px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                border: '1px solid #e5e7eb'
              }
            }}
            variant="filled"
          >
            <span className="first-letter:uppercase">{v.name}</span>
            <Button
              variant="subtle"
              size="xs"
              onClick={() => handleRemove(v.id)}
              styles={{ root: { padding: 0, width: '24px', height: '24px' } }}
            >
              <XIcon size={16} />
            </Button>
          </Badge>
        ))}
      </div>

      <Button
        onClick={handleSave}
        className="w-full"
        loading={isSaving}
        disabled={tempPracticeAreas.length === 0}
      >
        Save
      </Button>
    </div>
  )
}

export default PracticeAreas
