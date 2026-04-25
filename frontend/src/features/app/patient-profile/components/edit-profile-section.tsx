import { useState } from 'react'
import PersonalInfoSection from './personal-info-section'
import MedicalInfoSection from './medical-info-section'

const EditProfileSection = () => {
  const [activeTab, setActiveTab] = useState<string>('personal')

  return (
    <div className="w-full mx-auto p-8 bg-white">
      {/* Custom Segmented Control - Full Width */}
      <div className="mb-6 w-full">
        <div className="flex w-full rounded-lg border border-[#E4E5ED] bg-white p-1">
          <button
            type="button"
            onClick={() => setActiveTab('personal')}
            className={`flex-1 px-6 py-2.5 rounded-md font-poppins font-medium text-sm transition-all text-center ${
              activeTab === 'personal'
                ? 'bg-[#002FD4] text-white'
                : 'bg-white text-[#545D69] hover:bg-[#F4F6F9]'
            }`}
          >
            Personal Info
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('medical')}
            className={`flex-1 px-6 py-2.5 rounded-md font-poppins font-medium text-sm transition-all text-center ${
              activeTab === 'medical'
                ? 'bg-[#002FD4] text-white'
                : 'bg-white text-[#545D69] hover:bg-[#F4F6F9]'
            }`}
          >
            Medical Info
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'personal' && <PersonalInfoSection />}
      {activeTab === 'medical' && <MedicalInfoSection />}
    </div>
  )
}

export default EditProfileSection

