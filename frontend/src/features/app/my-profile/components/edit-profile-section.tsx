import { CaretDownIcon, CaretUpIcon, CheckIcon, PencilSimpleIcon } from "@phosphor-icons/react";
import { useState, useEffect, useRef } from "react";
import { useMyProfile } from "../hooks/use-my-profile";
import { useLanguages } from "@/hooks/use-languages";
import { useSpecializations } from "../hooks/use-specializations";
import { toast } from "react-toastify";

const EditProfileSection = () => {
  const { myProfile, updateProfile, isUpdatingProfile } = useMyProfile();
  const { languages } = useLanguages();
  const { specializations } = useSpecializations();
  const languageDropdownRef = useRef<HTMLDivElement>(null);
  const specializationDropdownRef = useRef<HTMLDivElement>(null);

  const [formData, setFormData] = useState({
    firstName: "",
    middleName: "",
    lastName: "",
    contactNumber: "",
    email: "",
    dateOfBirth: "",
    years_of_experience: "",
    education: "",
    specializations: [] as string[],
    languages: [] as string[],
    about: "",
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);

  const handleEditClick = () => fileInputRef.current?.click();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > MAX_IMAGE_SIZE_BYTES) {
      toast.error('Profile image must be 5 MB or smaller');
      e.target.value = ''; // clear the file input so the same file can be re-selected after shrinking
      return;
    }

    setSelectedImageFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewImage(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  // Pre-fill form correctly from backend data
  useEffect(() => {
    if (myProfile) {

      setFormData({
        firstName: myProfile.first_name || "",
        middleName: myProfile.middle_name || "",
        lastName: myProfile.last_name || "",
        contactNumber: myProfile.phone_number || "",
        email: myProfile.email || "",
        dateOfBirth: myProfile.date_of_birth || myProfile.dob || "",
        years_of_experience: myProfile.years_of_experience?.toString() || "",
        education: myProfile.education || "",
        about: myProfile.about || "",
        specializations: myProfile.specializations?.map((s: any) => s.id || s) || [],
        languages: myProfile.languages?.map((l: any) => l.id || l) || [],
      });
      setPreviewImage(myProfile.profile_img || myProfile.profile_img_url || null);
    }
  }, [myProfile]);

  const MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024 // 5 MB
  const MAX_ABOUT_LENGTH = 2000
  const MAX_NAME_LENGTH = 255
  const PHONE_REGEX = /^\d{10}$/

  const [showLanguageDropdown, setShowLanguageDropdown] = useState(false);
  const [showSpecializationDropdown, setShowSpecializationDropdown] = useState(false);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (languageDropdownRef.current && !languageDropdownRef.current.contains(event.target as Node)) {
        setShowLanguageDropdown(false);
      }
      if (specializationDropdownRef.current && !specializationDropdownRef.current.contains(event.target as Node)) {
        setShowSpecializationDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLanguageToggle = (langId: string) => {
    setFormData(prev => ({
      ...prev,
      languages: prev.languages.includes(langId)
        ? prev.languages.filter(l => l !== langId)
        : [...prev.languages, langId]
    }));
  };

  const handleSpecializationToggle = (specId: string) => {
    setFormData(prev => ({
      ...prev,
      specializations: prev.specializations.includes(specId)
        ? prev.specializations.filter(s => s !== specId)
        : [...prev.specializations, specId]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const firstName = formData.firstName.trim();
    const lastName = formData.lastName.trim();
    const middleName = formData.middleName.trim();
    const phone = formData.contactNumber.trim();
    const about = formData.about;

    if (firstName.length < 1 || firstName.length > MAX_NAME_LENGTH) {
      toast.error(`First name must be 1-${MAX_NAME_LENGTH} characters`);
      return;
    }
    if (lastName.length < 1 || lastName.length > MAX_NAME_LENGTH) {
      toast.error(`Last name must be 1-${MAX_NAME_LENGTH} characters`);
      return;
    }
    if (middleName && middleName.length > MAX_NAME_LENGTH) {
      toast.error(`Middle name must not exceed ${MAX_NAME_LENGTH} characters`);
      return;
    }
    if (phone && !PHONE_REGEX.test(phone)) {
      toast.error('Phone number must be exactly 10 digits');
      return;
    }
    if (about.length > MAX_ABOUT_LENGTH) {
      toast.error(`About must be ${MAX_ABOUT_LENGTH} characters or fewer`);
      return;
    }

    const payload = {
      first_name: firstName,
      middle_name: middleName, // empty string if not filled
      last_name: lastName,
      phone_number: phone,
      email: formData.email,
      dob: formData.dateOfBirth,
      years_of_experience: formData.years_of_experience,
      education: formData.education,
      about,
      specializations: formData.specializations,
      languages: formData.languages,
      profile_img: selectedImageFile || undefined,
    };

    updateProfile(payload, {
      onSuccess: () => toast.success("Profile updated successfully!"),
      onError: () => toast.error("Failed to update profile")
    });
  };

  const inputClass = `w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
    placeholder:text-[#A5ABB3D9] placeholder:font-medium
    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all`;

  const getInitial = () => formData.firstName ? formData.firstName.charAt(0).toUpperCase() : "?";

  const getSelectedLanguageNames = () => {
    return formData.languages
      .map(id => languages?.find((l: any) => l.id === id)?.language_name)
      .filter(Boolean)
      .join(', ') || "Choose languages";
  };

  const getSelectedSpecializationNames = () => {
    return formData.specializations
      .map(id => specializations?.find((s: any) => s.id === id)?.name)
      .filter(Boolean)
      .join(', ') || "Choose Specializations";
  };

  return (
    <div className="w-full mx-auto p-8 bg-white">
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
            <button type="button" onClick={handleEditClick} className="absolute bottom-0 right-0 bg-white rounded-full p-1 shadow-md">
              <PencilSimpleIcon size={20} className="text-[#002FD4]" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">First Name</label>
            <input type="text" value={formData.firstName} onChange={e => setFormData({ ...formData, firstName: e.target.value })} maxLength={MAX_NAME_LENGTH} className={inputClass} />
          </div>

          <div>
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Middle Name (Optional)</label>
            <input type="text" value={formData.middleName} onChange={e => setFormData({ ...formData, middleName: e.target.value })} maxLength={MAX_NAME_LENGTH} className={inputClass} />
          </div>

          <div>
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Last Name</label>
            <input type="text" value={formData.lastName} onChange={e => setFormData({ ...formData, lastName: e.target.value })} maxLength={MAX_NAME_LENGTH} className={inputClass} />
          </div>

          <div>
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Contact Number</label>
            <input type="tel" inputMode="numeric" pattern="\d{10}" maxLength={10} value={formData.contactNumber} onChange={e => setFormData({ ...formData, contactNumber: e.target.value.replace(/\D/g, '') })} placeholder="9876543210" className={inputClass} />
          </div>

          <div>
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Email</label>
            <input type="email" value={formData.email} readOnly className={`${inputClass} bg-gray-50 cursor-not-allowed`} />
          </div>

          <div>
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Date of Birth</label>
            <input type="date" value={formData.dateOfBirth} readOnly className={`${inputClass} bg-gray-50 cursor-not-allowed`} />
          </div>

          <div>
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Years of Experience</label>
            <input type="text" value={formData.years_of_experience} onChange={e => setFormData({ ...formData, years_of_experience: e.target.value })} placeholder="10" className={inputClass} />
          </div>

          <div>
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Education</label>
            <input type="text" value={formData.education} onChange={e => setFormData({ ...formData, education: e.target.value })} placeholder="MBBS, MD in Cardiology" className={inputClass} />
          </div>

          {/* Specializations Multi-select */}
          <div className="relative">
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Specializations</label>
            <button type="button" onClick={() => setShowSpecializationDropdown(prev => !prev)}
              className="w-full px-4 py-3 border border-[#E4E1FA] rounded-md flex justify-between items-center text-left bg-white">
              <span className="font-poppins text-sm text-[#0F1011] truncate">
                {getSelectedSpecializationNames()}
              </span>
              {showSpecializationDropdown ? <CaretUpIcon size={20} /> : <CaretDownIcon size={20} />}
            </button>
            {showSpecializationDropdown && (
              <div ref={specializationDropdownRef} className="absolute z-50 w-full mt-1 bg-white rounded-lg shadow-xl border border-gray-200 max-h-60 overflow-y-auto">
                {specializations?.map((spec: any) => (
                  <button key={spec.id} type="button" onClick={() => handleSpecializationToggle(spec.id)}
                    className="w-full px-4 py-3 text-left hover:bg-[#F4F6F9] flex justify-between items-center">
                    <span className="font-poppins text-sm text-[#0F1011]">{spec.name}</span>
                    {formData.specializations.includes(spec.id) && <CheckIcon className="text-[#002FD4]" size={18} />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Languages Multi-select */}
          <div className="relative">
            <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">Languages Known</label>
            <button type="button" onClick={() => setShowLanguageDropdown(prev => !prev)}
              className="w-full px-4 py-3 border border-[#E4E1FA] rounded-md flex justify-between items-center text-left bg-white">
              <span className="font-poppins text-sm text-[#0F1011] truncate">
                {getSelectedLanguageNames()}
              </span>
              {showLanguageDropdown ? <CaretUpIcon size={20} /> : <CaretDownIcon size={20} />}
            </button>
            {showLanguageDropdown && (
              <div ref={languageDropdownRef} className="absolute z-50 w-full mt-1 bg-white rounded-lg shadow-xl border border-gray-200 max-h-60 overflow-y-auto">
                {languages?.map((lang: any) => (
                  <button key={lang.id} type="button" onClick={() => handleLanguageToggle(lang.id)}
                    className="w-full px-4 py-3 text-left hover:bg-[#F4F6F9] flex justify-between items-center">
                    <span className="font-poppins text-sm text-[#0F1011]">{lang.language_name}</span>
                    {formData.languages.includes(lang.id) && <CheckIcon className="text-[#002FD4]" size={18} />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Bio */}
        <div className="mt-6">
          <label className="block mb-1 font-poppins font-medium text-[14px] text-[#545D69]">About / Bio</label>
          <textarea
            value={formData.about}
            onChange={e => setFormData({ ...formData, about: e.target.value })}
            placeholder="Experienced cardiologist with 10+ years of practice..."
            rows={5}
            maxLength={MAX_ABOUT_LENGTH}
            className={`${inputClass} resize-none`}
          />
          <div className="text-xs text-gray-400 mt-1 text-right">
            {formData.about.length}/{MAX_ABOUT_LENGTH}
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8">
          <button
            type="submit"
            disabled={isUpdatingProfile}
            className="px-6 py-3 rounded-lg bg-[#002FD4] text-white font-poppins font-semibold text-sm hover:bg-[#001FB8] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUpdatingProfile ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditProfileSection;