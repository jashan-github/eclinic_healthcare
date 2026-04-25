import { useState, type FC } from 'react'
import { FunnelIcon, MagnifyingGlassIcon, XIcon } from '@phosphor-icons/react'
import PendingTab from '../tabs/pending-tab'
import ProcessedTab from '../tabs/processed-tab'

const RequestsLayout: FC = () => {
  const [activeTab, setActiveTab] = useState('pending')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortAsc, setSortAsc] = useState<boolean | null>(null)
  // const [consultType, setConsultType] = useState<'online' | 'offline' | null>(null)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  // const [isMenuOpen, setIsMenuOpen] = useState(false)
  // const [consultExpanded, setConsultExpanded] = useState(false)

  const tabs = [
    { label: 'Pending', value: 'pending', component: <PendingTab searchTerm={searchTerm} sortAsc={sortAsc} /> },
    { label: 'Processed', value: 'processed', component: <ProcessedTab searchTerm={searchTerm} sortAsc={sortAsc} /> },
  ]

  return (
    <div className="h-full flex flex-col rounded-lg border border-gray-300 overflow-auto">

      <div className="bg-[#002FD4] p-1.5 flex items-center">

        {tabs.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => setActiveTab(value)}
            className={`
              px-2 py-2 rounded-md transition-all hover:cursor-pointer 
              ${activeTab === value ? 'text-white' : 'text-gray-400'}
            `}
          >
            <div className='font-poppins text-[13px] leading-5 font-bold'>
              {label}
            </div>
          </button>
        ))}

        <div className="ml-auto flex items-center">

          {isSearchOpen ? (
            <div className="flex items-center bg-white/20 rounded-md">
              <MagnifyingGlassIcon size={18} className="ml-3 text-white/70" />
              <input
                type="text"
                placeholder="Search requests..."
                autoFocus
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-64 px-4 py-2.5 text-sm bg-transparent text-white placeholder-white/70 outline-none font-poppins"
              />
              <button
                onClick={() => { setSearchTerm(''); setIsSearchOpen(false) }}
                className="p-2 hover:bg-white/20 rounded transition"
              >
                <XIcon size={18} weight="bold" className="text-white" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsSearchOpen(true)}
              className="p-2 text-white hover:bg-white/10 rounded-md transition"
            >
              <MagnifyingGlassIcon size={20} weight="regular" />
            </button>
          )}

          <button
            onClick={() => setSortAsc(prev => prev === null ? true : prev === true ? false : null)}
            className="p-2 text-white hover:bg-white/10 rounded-md transition"
          >
            <FunnelIcon size={20} weight={sortAsc !== null ? "fill" : "regular"} />
          </button>

          {/* <div className="relative">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 text-white hover:bg-white/10 rounded-md transition"
            >
              <DotsThreeVerticalIcon size={20} weight="regular" />
            </button>

            {isMenuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setIsMenuOpen(false)} />

                <div className="absolute right-0 top-10 w-64 bg-white rounded-lg shadow-2xl z-50 text-left overflow-hidden">

                  <button
                    onClick={() => console.log('Date button clicked')}
                    className="w-full px-3 py-2 flex items-center justify-between"
                  >
                    <span className="font-poppins text-[13px] leading-5 text-black capitalize">Date</span>
                  </button>

                  <div>
                    <button
                      onClick={() => setConsultExpanded(!consultExpanded)}
                      className="w-full px-3 py-2 flex items-center justify-between"
                    >
                      <span className="font-poppins text-[13px] leading-5 text-black capitalize">Consultation</span>
                      {consultExpanded ? (
                        <CaretUp size={14} weight="bold" className="text-gray-500" />
                      ) : (
                        <CaretDown size={14} weight="bold" className="text-gray-500" />
                      )}
                    </button>

                    {consultExpanded && (
                      <div>
                        <label className="flex items-center px-3 py-1.5 cursor-pointer select-none">
                          <input
                            type="radio"
                            name="c"
                            checked={consultType === 'online'}
                            onChange={() => setConsultType(consultType === 'online' ? null : 'online')}
                            className="w-3 h-3 text-[#002FD4] cursor-pointer"
                          />
                          <span className="ml-2 font-poppins text-[13px] leading-5 text-black capitalize">Online</span>
                        </label>

                        <label className="flex items-center px-3 py-1.5 cursor-pointer select-none">
                          <input
                            type="radio"
                            name="c"
                            checked={consultType === 'offline'}
                            onChange={() => setConsultType(consultType === 'offline' ? null : 'offline')}
                            className="w-3 h-3 text-[#002FD4] cursor-pointer"
                          />
                          <span className="ml-2 font-poppins text-[13px] leading-5 text-black capitalize">Offline</span>
                        </label>
                      </div>
                    )}
                  </div>

                  <button className="w-full px-3 py-2 flex items-center">
                    <span className="font-poppins text-[13px] leading-5 text-black capitalize">Patient History</span>
                  </button>
                </div>
              </>
            )}
          </div> */}
        </div>
      </div>

      <div className="flex-1 p-4 bg-[#F4F6F9]">
        {tabs.find(tab => tab.value === activeTab)?.component}
      </div>
    </div>
  )
}

export default RequestsLayout