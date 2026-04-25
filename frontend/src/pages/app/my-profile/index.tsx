import EditProfileSection from '@/features/app/my-profile/components/edit-profile-section'
import DoctorIntro from '@/features/app/my-profile/components/my-profile/doctor-intro'
import HeroSection from '@/features/app/my-profile/components/my-profile/hero-section'
import LanguageShow from '@/features/app/my-profile/components/my-profile/language-show'
import SpecializationsList from '@/features/app/my-profile/components/my-profile/specialization-list'
// import WorkspaceName from '@/features/app/my-profile/components/my-profile/workspace-name'
import SecondaryHeader from '@/features/app/my-profile/components/secondary-header'
import { useState, type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'

const MyProfilePage: FC = (): ReactElement => {
  const [isEditing, setIsEditing] = useState<boolean>(false)

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
          {/* Profile Image */}
          <HeroSection />
          <LanguageShow />
          <DoctorIntro />
          <SpecializationsList />
        </main>
      )}
    </div>
  )
}

export default MyProfilePage
