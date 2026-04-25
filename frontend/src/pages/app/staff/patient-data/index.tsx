import PatientDataContent from "@/features/app/staff/components/patient-data-content";

export default function PatientData() {
    return (
        <div className="bg-[#F4F6F9] p-6 h-screen flex flex-col overflow-hidden">
            {/* Patients Contact Details */}
            <div className='bg-white p-6 rounded-lg shadow-[6px_7px_20px_0px_#0000001A] flex flex-col flex-1 min-h-0 overflow-hidden'>
                <div className="font-poppins text-xl font-semibold leading-6 text-[#0F1011]">
                    Patients Contact Details
                </div>
                <div className="font-poppins text-sm text-slate-500 mt-1 mb-6">
                    Lorem ipsum dolor sit amet, consectetur adipiscing
                </div>

                <div className="flex-1 min-h-0 overflow-hidden">
                    <PatientDataContent />
                </div>
            </div>
        </div>
    )
}

