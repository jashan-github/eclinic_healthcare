import { PencilSimpleIcon } from '@phosphor-icons/react'
import { useState, useEffect, useRef } from 'react'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { usePatientProfile } from '../hooks/use-patient-profile'
import { BLOOD_TYPES } from '@/utils/blood-types-options'
import { useLanguages } from '@/hooks/use-languages'
import { useLocation } from '@/features/app/my-profile/hooks/use-locations'

// Backend-aligned validation: see swagger spec for `update-patient-profile`.
const personalInfoSchema = z
  .object({
    firstName: z
      .string()
      .trim()
      .min(1, 'First name is required')
      .max(255, 'First name must be 255 characters or fewer'),
    lastName: z
      .string()
      .trim()
      .min(1, 'Last name is required')
      .max(255, 'Last name must be 255 characters or fewer'),
    phoneNumber: z
      .string()
      .trim()
      .max(20, 'Contact number must be 20 characters or fewer'),
    dateOfBirth: z.string().optional()
  })
  .refine(
    (data) => {
      if (!data.dateOfBirth) return true
      const d = new Date(data.dateOfBirth)
      return !Number.isNaN(d.getTime()) && d.getTime() <= Date.now()
    },
    { message: 'Date of birth cannot be in the future', path: ['dateOfBirth'] }
  )

const MARITAL_STATUS_OPTIONS = [
  { label: 'Single', value: 'Single' },
  { label: 'Married', value: 'Married' },
  { label: 'Divorced', value: 'Divorced' },
  { label: 'Widowed', value: 'Widowed' },
  { label: 'Separated', value: 'Separated' }
] as const

const PersonalInfoSection = () => {
  const { patientProfile, updateProfile, isUpdatingProfile } = usePatientProfile()
  const { languages } = useLanguages()
  const [selectedCountryId, setSelectedCountryId] = useState<string>('')
  const [selectedStateId, setSelectedStateId] = useState<string>('')
  const [selectedCityId, setSelectedCityId] = useState<string>('')
  const [selectedLanguageId, setSelectedLanguageId] = useState<string>('')

  // Initialize IDs from patientProfile first
  useEffect(() => {
    if (patientProfile) {
      if (patientProfile.country_id) setSelectedCountryId(patientProfile.country_id)
      if (patientProfile.state_id) setSelectedStateId(patientProfile.state_id)
      if (patientProfile.city_id) setSelectedCityId(patientProfile.city_id)
      if (patientProfile.preferred_language_id) setSelectedLanguageId(patientProfile.preferred_language_id)
    }
  }, [patientProfile])

  const {
    countries,
    states,
    cities,
    isLoadingCountries,
    isLoadingStates,
    isLoadingCities,
  } = useLocation(selectedCountryId, selectedStateId)

  const [formData, setFormData] = useState({
    firstName: '',
    middleName: '',
    lastName: '',
    email: '',
    phoneCode: '',
    phoneNumber: '',
    gender: '',
    dateOfBirth: '',
    addressLine1: '',
    postalCode: '',
    bloodType: '',
    emergencyContactNumber: '',
    familyContactNumber: '',
    occupation: '',
    maritalStatus: '',
  })

  const fileInputRef = useRef<HTMLInputElement>(null)
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null)

  const handleEditClick = () => fileInputRef.current?.click()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImageFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setPreviewImage(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  // Fill form with latest backend data
  useEffect(() => {
    if (patientProfile) {
      setFormData({
        firstName: patientProfile.first_name || patientProfile.full_name?.split(' ')[0] || '',
        middleName: patientProfile.middle_name || '',
        lastName: patientProfile.last_name || patientProfile.full_name?.split(' ').slice(1).join(' ') || '',
        email: patientProfile.email || '',
        phoneCode: patientProfile.phone_code?.toString() || '',
        phoneNumber: patientProfile.contact_number || patientProfile.phone_number || '',
        gender: patientProfile.gender || '',
        dateOfBirth: patientProfile.date_of_birth || patientProfile.dob || '',
        addressLine1: patientProfile.address_line_1 || patientProfile.address || '',
        postalCode: patientProfile.postal_code || patientProfile.zip_code || '',
        bloodType: patientProfile.blood_type || patientProfile.blood_group || '',
        emergencyContactNumber: patientProfile.emergency_contact_number || patientProfile.emergency_number || '',
        familyContactNumber: patientProfile.family_contact_number || '',
        occupation: patientProfile.occupation || '',
        maritalStatus: patientProfile.marital_status || '',
      })
      
      // Set IDs for dropdowns from backend response
      if (patientProfile.country_id) setSelectedCountryId(patientProfile.country_id)
      if (patientProfile.state_id) setSelectedStateId(patientProfile.state_id)
      if (patientProfile.city_id) setSelectedCityId(patientProfile.city_id)
      if (patientProfile.preferred_language_id) setSelectedLanguageId(patientProfile.preferred_language_id)
      
      setPreviewImage(patientProfile.profile_img_url || patientProfile.profile_img || null)
    }
  }, [patientProfile])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const parsed = personalInfoSchema.safeParse({
      firstName: formData.firstName,
      lastName: formData.lastName,
      phoneNumber: formData.phoneNumber,
      dateOfBirth: formData.dateOfBirth
    })
    if (!parsed.success) {
      parsed.error.issues.forEach((issue) => toast.error(issue.message))
      return
    }

    // Create payload exactly as swagger expects
    const payload = {
      first_name: formData.firstName.trim(),
      middle_name: formData.middleName,
      last_name: formData.lastName.trim(),
      contact_number: formData.phoneNumber.trim(),
      gender: formData.gender,
      date_of_birth: patientProfile?.date_of_birth || patientProfile?.dob || formData.dateOfBirth,
      address_line_1: formData.addressLine1,
      postal_code: formData.postalCode,
      country_id: selectedCountryId,
      state_id: selectedStateId,
      city_id: selectedCityId,
      blood_type: formData.bloodType,
      emergency_contact_number: formData.emergencyContactNumber,
      family_contact_number: formData.familyContactNumber,
      occupation: formData.occupation,
      marital_status: formData.maritalStatus,
      preferred_language_id: selectedLanguageId,
      avatar: selectedImageFile || undefined
    }

    updateProfile(payload, {
      onSuccess: () => toast.success('Profile updated!'),
      onError: () => toast.error('Failed to update')
    })
  }

  const inputClass = `w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
    placeholder:text-[#A5ABB3D9] placeholder:font-medium
    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all`

  const getInitial = () => {
    const name = formData.firstName || formData.lastName
    return name ? name.charAt(0).toUpperCase() : '?'
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="font-poppins font-bold text-[24px] leading-[32px] text-[#0F1011] mb-2">
          Personal Information
        </h2>
        <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
          Update your personal details and contact information.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Profile Image */}
        <div className="mb-8">
          <div className="relative w-[120px] h-[120px] rounded-full bg-primary/10 flex items-center justify-center">
            {previewImage ? (
              <img src={previewImage} alt="Profile" className="w-full h-full rounded-full object-cover" />
            ) : (
              <span className="text-3xl font-bold text-primary">{getInitial()}</span>
            )}
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
            <button type="button" onClick={handleEditClick}
              className="absolute bottom-0 right-0 w-[40px] h-[40px] rounded-full bg-white border border-[#D1D1D1] 
                         flex items-center justify-center hover:bg-accent transition-colors">
              <PencilSimpleIcon size={20} weight="fill" />
            </button>
          </div>
        </div>

        {/* Form Fields - Two Columns */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">First Name</label>
              <input
                type="text"
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                placeholder="Mick"
                maxLength={255}
                className={inputClass}
                required
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Middle Name</label>
              <input
                type="text"
                value={formData.middleName}
                onChange={(e) => setFormData({ ...formData, middleName: e.target.value })}
                placeholder="Middle"
                maxLength={255}
                className={inputClass}
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Last Name</label>
              <input
                type="text"
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                placeholder="Will"
                maxLength={255}
                className={inputClass}
                required
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Email</label>
              <input
                type="email"
                value={formData.email}
                readOnly
                className={`${inputClass} bg-gray-50 cursor-not-allowed`}
                placeholder="mickwill@gmail.com"
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Contact Number</label>
              <input
                type="tel"
                value={formData.phoneNumber}
                onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                placeholder="+1 (721) 544-2275"
                maxLength={20}
                className={inputClass}
                required
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Gender</label>
              <select
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                className={inputClass}
              >
                <option value="">Choose gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Address Line 1</label>
              <input
                type="text"
                value={formData.addressLine1}
                onChange={(e) => setFormData({ ...formData, addressLine1: e.target.value })}
                placeholder="123 Main Street"
                className={inputClass}
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Emergency Contact Number</label>
              <input
                type="tel"
                value={formData.emergencyContactNumber}
                onChange={(e) => setFormData({ ...formData, emergencyContactNumber: e.target.value })}
                placeholder="+1 (721) 555-1234"
                className={inputClass}
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Blood Type</label>
              <select
                value={formData.bloodType}
                onChange={(e) => setFormData({ ...formData, bloodType: e.target.value })}
                className={inputClass}
              >
                <option value="">Choose your blood type</option>
                {BLOOD_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Occupation</label>
              <input
                type="text"
                value={formData.occupation}
                onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                placeholder="Software Engineer"
                className={inputClass}
              />
            </div>

            {/* Address Fields */}
            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Country</label>
              <select
                value={selectedCountryId}
                onChange={(e) => {
                  setSelectedCountryId(e.target.value)
                  setSelectedStateId('')
                  setSelectedCityId('')
                }}
                className={inputClass}
              >
                <option value="">{isLoadingCountries ? 'Loading...' : 'Select country'}</option>
                {countries.map(country => (
                  <option key={country.id} value={country.id}>
                    {country.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">City</label>
              <select
                value={selectedCityId}
                onChange={(e) => setSelectedCityId(e.target.value)}
                disabled={!selectedStateId}
                className={inputClass}
              >
                <option value="">{isLoadingCities ? 'Loading...' : 'Select city'}</option>
                {cities.map(city => (
                  <option key={city.id} value={city.id}>
                    {city.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Date of Birth</label>
              <input
                type="date"
                value={formData.dateOfBirth || ''}
                readOnly
                className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                  font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                  bg-gray-50 cursor-not-allowed"
                style={{ height: '44px' }}
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Family Contact Number</label>
              <input
                type="tel"
                value={formData.familyContactNumber}
                onChange={(e) => setFormData({ ...formData, familyContactNumber: e.target.value })}
                placeholder="+1 (721) 555-5678"
                className={inputClass}
              />
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Marital Status</label>
              <select
                value={formData.maritalStatus}
                onChange={(e) => setFormData({ ...formData, maritalStatus: e.target.value })}
                className={inputClass}
              >
                <option value="">Choose status</option>
                {MARITAL_STATUS_OPTIONS.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Preferred Language</label>
              <select
                value={selectedLanguageId}
                onChange={(e) => setSelectedLanguageId(e.target.value)}
                className={inputClass}
              >
                <option value="">Choose languages</option>
                {languages?.map((lang: any) => (
                  <option key={lang.id} value={lang.id}>
                    {lang.language_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Address Fields */}
            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">State</label>
              <select
                value={selectedStateId}
                onChange={(e) => {
                  setSelectedStateId(e.target.value)
                  setSelectedCityId('')
                }}
                disabled={!selectedCountryId}
                className={inputClass}
              >
                <option value="">{isLoadingStates ? 'Loading...' : 'Select state'}</option>
                {states.map(state => (
                  <option key={state.id} value={state.id}>
                    {state.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Postal Code</label>
              <input
                type="text"
                value={formData.postalCode}
                onChange={(e) => setFormData({ ...formData, postalCode: e.target.value })}
                placeholder="10001"
                className={inputClass}
              />
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8">
          <button
            type="submit"
            disabled={isUpdatingProfile}
            className="w-[140px] h-11 rounded-lg bg-[#002FD4] text-white font-poppins font-semibold text-sm hover:bg-[#001FB8] transition-colors disabled:opacity-50"
          >
            {isUpdatingProfile ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default PersonalInfoSection