// components/settings/GeneralSettings.tsx

const GeneralSettings = () => {
  // Static data - read-only display
  const settingsData = {
    clinicName: 'Purehealthbv',
    timezone: 'UTC-05:00 (EST)',
    defaultLanguage: 'English',
    currency: 'USD ($)',
  }

  return (
    <div className="w-full bg-white rounded-2xl p-6">
      <div className="mb-10">
        <h1 className="font-poppins font-semibold text-xl leading-6 text-[#0F1011]">General Settings</h1>
        <p className="mt-1 font-poppins font-normal text-sm leading-5 text-[#64748B]">View basic system settings</p>
      </div>

      <div className="space-y-8">
        {/* Clinic Name */}
        <div>
          <div className="font-poppins font-semibold text-sm leading-[14px] text-[#0F1011] mb-2">
            Clinic Name
          </div>
          <div className="font-poppins font-normal text-base leading-6 text-[#64748B]">
            {settingsData.clinicName}
          </div>
        </div>

        {/* Timezone */}
        <div>
          <div className="font-poppins font-semibold text-sm leading-[14px] text-[#0F1011] mb-2">
            Timezone
          </div>
          <div className="font-poppins font-normal text-base leading-6 text-[#64748B]">
            {settingsData.timezone}
          </div>
        </div>

        {/* Default Language */}
        <div>
          <div className="font-poppins font-semibold text-sm leading-[14px] text-[#0F1011] mb-2">
            Default Language
          </div>
          <div className="font-poppins font-normal text-base leading-6 text-[#64748B]">
            {settingsData.defaultLanguage}
          </div>
        </div>

        {/* Currency */}
        <div>
          <div className="font-poppins font-semibold text-sm leading-[14px] text-[#0F1011] mb-2">
            Currency
          </div>
          <div className="font-poppins font-normal text-base leading-6 text-[#64748B]">
            {settingsData.currency}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GeneralSettings