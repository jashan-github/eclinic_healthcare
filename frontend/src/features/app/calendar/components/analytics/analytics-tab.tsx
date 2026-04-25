// src/components/AnalyticsCard.tsx
import { DotsThreeOutlineVertical } from '@phosphor-icons/react'
import { type FC, type ReactElement, useState, useRef, useEffect } from 'react'

interface AnalyticsCardProps {
  title: string
  data: React.ReactNode
}

const AnalyticsCard: FC<AnalyticsCardProps> = ({ title, data }): ReactElement => {
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsPanelOpen(false)
      }
    }

    if (isPanelOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isPanelOpen])

  return (
    <div
      className="relative flex w-full items-start justify-between p-4 bg-white rounded-lg"
      style={{
        minHeight: '136px',
        maxHeight: '33554400px',
        boxShadow: '6px 7px 20px 0px #0000001A',
      }}
    >
      {/* Title + Data */}
      <div className="flex flex-col gap-2">
        <span
          className="text-[#0F1011]"
          style={{
            fontFamily: 'Poppins, sans-serif',
            fontWeight: 500,
            fontSize: '16px',
            lineHeight: '25.14px',
            letterSpacing: '0%',
          }}
        >
          {title}
        </span>
        <div className="font-poppins font-medium text-base leading-6 text-[#0F1011]">{data}</div>
      </div>

      {/* Three Dots Button */}
      <button
        ref={buttonRef}
        onClick={() => setIsPanelOpen((prev) => !prev)}
        className="text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
        aria-label="More options"
      >
        <DotsThreeOutlineVertical className="w-5 h-5" weight="fill" />
      </button>

      {/* Dropdown Panel */}
      {isPanelOpen && (
        <div
          ref={panelRef}
          className="absolute right-0 top-8 mt-2 w-64 bg-white shadow-lg border border-gray-200 p-4 z-50"
          style={{
            boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.1)',
          }}
        >
          <p className="text-sm text-gray-500 text-center">Panel is empty</p>
        </div>
      )}
    </div>
  )
}

export default AnalyticsCard
