import { type FC } from 'react'
import { CalendarBlank, List } from '@phosphor-icons/react'

type Props = {
  value: 'list' | 'calendar'
  onChange: (v: 'list' | 'calendar') => void
}

const ViewToggle: FC<Props> = ({ value, onChange }) => {
  return (
<div className="inline-flex items-center">
  {/* List View Button */}
  <button
    type="button"
    className={`inline-flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors
      ${value === 'list' 
        ? 'bg-[#002FD4] text-white shadow-sm rounded-l-lg' 
        : 'text-gray-700 bg-[#F4F6F9] hover:bg-gray-200 rounded-l-lg'
      }`}
    style={{
      width: '163px',
      height: '40px',
      padding: '12px 16px',
      borderTopLeftRadius: '8px',
      borderBottomLeftRadius: '8px',
      fontFamily: 'Poppins',
      fontWeight: 600,
      fontSize: '14px',
      lineHeight: '21px',
      letterSpacing: '0%',
      verticalAlign: 'middle',
    }}
    onClick={() => onChange('list')}
  >
    <List size={16} weight="bold" />
    <span>List View</span>
  </button>

  {/* Calendar View Button */}
  <button
    type="button"
    className={`inline-flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ml-px
      ${value === 'calendar' 
        ? 'bg-[#002FD4] text-white shadow-sm rounded-r-lg' 
        : 'text-gray-700 bg-[#F4F6F9] hover:bg-gray-200 rounded-r-lg'
      }`}
    style={{
      width: '163px',
      height: '40px',
      padding: '12px 16px',
      borderTopRightRadius: '8px',
      borderBottomRightRadius: '8px',
      fontFamily: 'Poppins',
      fontWeight: 600,
      fontSize: '14px',
      lineHeight: '21px',
      letterSpacing: '0%',
      verticalAlign: 'middle',
    }}
    onClick={() => onChange('calendar')}
  >
    <CalendarBlank size={16} weight="bold" />
    <span>Calendar View</span>
  </button>
</div>
  )
}

export default ViewToggle
