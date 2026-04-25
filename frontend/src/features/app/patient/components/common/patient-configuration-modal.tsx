import BaseSideSheet from '@/components/orvo/base-side-sheet'
import { Tabs } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import PatientFields from './patient-fields'
import PatientMedicalHistory from './patient-medical-history'

const TABS = {
  PATIENT_FIELDS: 'patient-fields',
  MEDICAL_HISTORY: 'medical-history'
}

interface PatientConfigurationModalProps {
  isOpen: boolean
  setIsOpen: (isOpen: boolean) => void
}

const PatientConfigurationModal: FC<PatientConfigurationModalProps> = ({
  isOpen,
  setIsOpen
}): ReactElement => {
  return (
    <BaseSideSheet
      isOpen={isOpen}
      onOpenChange={setIsOpen}
      title="Configure Add Patient"
    >
      <Tabs
        variant={'outline'}
        defaultValue={TABS.PATIENT_FIELDS}
      >
        <Tabs.List>
          <Tabs.Tab value={TABS.PATIENT_FIELDS}>Patient</Tabs.Tab>
          <Tabs.Tab value={TABS.MEDICAL_HISTORY}>Medical History</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value={TABS.PATIENT_FIELDS}>
          <PatientFields />
        </Tabs.Panel>
        <Tabs.Panel value={TABS.MEDICAL_HISTORY}>
          <PatientMedicalHistory />
        </Tabs.Panel>
      </Tabs>
    </BaseSideSheet>
  )
}

export default PatientConfigurationModal
