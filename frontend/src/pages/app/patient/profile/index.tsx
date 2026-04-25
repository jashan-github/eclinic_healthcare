import EditProfileSection from '@/features/app/patient-profile/components/edit-profile-section'
import SecondaryHeader from '@/features/app/patient-profile/components/secondary-header'
import { useState, type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'

const PatientProfilePage: FC = (): ReactElement => {
  const [isEditing, setIsEditing] = useState<boolean>(true) // Start in edit mode for new patients

  return (
    <div className="h-[calc(100vh-60px)] overflow-y-scroll scroll-smooth bg-[#F4F6F9]">
      <SecondaryHeader
        isEditing={isEditing}
        setIsEditing={setIsEditing}
        onBack={() =>
          isEditing ? setIsEditing(false) : toast.error('No Action Specified')
        }
      />

      {/* Main Section */}
      {isEditing ? (
        <EditProfileSection />
      ) : (
        <main className="bg-[#F4F6F9] w-full h-full pt-xl px-20 mb-20 flex flex-col gap-5">
          {/* Profile View - Can be added later */}
          <div className="bg-white rounded-lg p-6">
            <p className="text-gray-500">Profile view coming soon</p>
          </div>
        </main>
      )}
    </div>
  )
}

export default PatientProfilePage

