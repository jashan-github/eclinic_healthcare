import { Combobox, Input, InputBase, useCombobox } from '@mantine/core'
import { FunnelIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

const presets = [
  {
    label: 'Today',
    value: 'today'
  },
  {
    label: 'Yesterday',
    value: 'yesterday'
  },
  {
    label: 'Last 7 Days',
    value: 'lastSevenDays'
  }
]

const DateRangePresetsDropdown: FC = (): ReactElement => {
  const [selectedPreset, setSelectedPreset] = useState<string>('today')

  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption()
  })

  const options = presets.map((item) => (
    <Combobox.Option
      value={item.value}
      key={item.value}
    >
      {item.label}
    </Combobox.Option>
  ))

  return (
    <Combobox
      store={combobox}
      withinPortal={false}
      onOptionSubmit={(val) => {
        setSelectedPreset(val)
        combobox.closeDropdown()
      }}
    >
      <Combobox.Target>
        <InputBase
          component="button"
          type="button"
          leftSection={<FunnelIcon />}
          pointer
          rightSection={<Combobox.Chevron />}
          onClick={() => combobox.toggleDropdown()}
          rightSectionPointerEvents="none"
        >
          {selectedPreset || <Input.Placeholder>Pick value</Input.Placeholder>}
        </InputBase>
      </Combobox.Target>

      <Combobox.Dropdown>
        <Combobox.Options>{options}</Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  )
}

export default DateRangePresetsDropdown
