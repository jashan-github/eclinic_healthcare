import { SegmentedControl } from '@mantine/core'
import React from 'react'

interface SegmentTabsProps {
  value: string
  onChange: (v: string) => void
}

const SegmentTabs: React.FC<SegmentTabsProps> = ({ value, onChange }) => {
  const data = [
    { label: 'Healthcare Provider', value: 'Doctor' },
    { label: 'Patient', value: 'Patient' },
    { label: 'Staff', value: 'Staff' }
  ]

  return (
    <SegmentedControl
      bg={'white'}
      value={value}
      color="primary"
      onChange={onChange}
      data={data}
      fullWidth
      radius={'md'}
      size="sm"
      className="mx-auto max-w-[500px] shadow-[6px_7px_20px_0px_rgba(0,0,0,0.10)]"
      withItemsBorders={false}
    />
  )
}

export default SegmentTabs
