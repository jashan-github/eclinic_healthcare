import { type FC, type ReactElement, useState, Children, isValidElement } from 'react'
import { MagnifyingGlass, X, Funnel} from '@phosphor-icons/react'
import React from 'react'

interface Tab {
  label: string
  value: string
  content: ReactElement
}

interface WebinarTabsProps {
  tabs: Tab[]
}

const WebinarTabs: FC<WebinarTabsProps> = ({ tabs }) => {
  const [activeTab, setActiveTab] = useState(tabs[0]?.value || 'upcoming')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortAsc, setSortAsc] = useState<boolean | null>(null)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const currentTab = tabs.find(t => t.value === activeTab)
  const rawContent = currentTab?.content

  const renderContent = () => {
    if (!rawContent) return null

    return Children.map(rawContent, child => {
      if (isValidElement(child)) {
        return React.cloneElement(child as React.ReactElement<any>, {
          searchTerm,
          sortAsc
        })
      }
      return child
    })
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">

      <div className="bg-[#002FD4] p-1.5 flex items-center rounded-md">
        <div className="flex gap-1">
          {tabs.map(({ label, value }) => (
            <button
              key={value}
              onClick={() => setActiveTab(value)}
              className={`
                hover:cursor-pointer px-5 py-2 rounded-md transition-all
                ${activeTab === value ? 'text-white' : 'text-gray-500 hover:text-white'}
              `}
            >
              <div className='font-poppins text-[13px] leading-5 font-bold'>
                {label}
              </div>
            </button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-1">

          {isSearchOpen ? (
            <div className="flex items-center bg-white/20 backdrop-blur-sm rounded-lg border border-white/30">
              <MagnifyingGlass size={18} className="ml-3 text-white/70" />
              <input
                type="text"
                placeholder="Search webinars..."
                autoFocus
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-48 px-3 py-1.5 text-sm bg-transparent text-white placeholder-white/70 outline-none font-poppins"
              />
              <button
                onClick={() => {
                  setSearchTerm('')
                  setIsSearchOpen(false)
                }}
                className="p-2 hover:bg-white/20 rounded-lg transition"
              >
                <X size={18} weight="bold" className="text-white" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsSearchOpen(true)}
              className="p-2 text-white hover:bg-white/10 rounded-md transition"
            >
              <MagnifyingGlass size={20} weight="regular" />
            </button>
          )}

          <button
            onClick={() => setSortAsc(prev => prev === null ? true : prev === true ? false : null)}
            className="p-2 text-white hover:bg-white/10 rounded-md transition"
          >
            <Funnel size={20} weight={sortAsc !== null ? "fill" : "regular"} />
          </button>

          <div className="relative">
            {isMenuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setIsMenuOpen(false)} />

                
              </>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 py-4">
        {renderContent()}
      </div>
    </div>
  )
}

export default WebinarTabs