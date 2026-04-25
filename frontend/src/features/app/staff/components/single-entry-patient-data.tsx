// single-entry.tsx

import { Phone, EnvelopeSimpleIcon } from '@phosphor-icons/react'

interface SingleEntryProps {
    name: string
    email: string
    age: number
    gender: 'Male' | 'Female'
    contactNumber: string
    emergencyContact: string
    familyContact: string
    // Optional props (not used in component but kept for backward compatibility)
    type?: 'Teleconsultation' | 'In-Clinic'
    time?: string
    doctor?: string
    duration?: number
    status?: 'Confirmed' | 'Pending'
    paymentStatus?: 'Paid' | 'Unpaid' | 'Refunded'
    paymentMethod?: string
}

const SingleEntry: React.FC<SingleEntryProps> = ({
    name,
    email,
    age,
    gender,
    contactNumber,
    emergencyContact,
    familyContact,
}) => {

    // First letter of name for avatar
    const avatarLetter = name.charAt(0).toUpperCase()

    return (
        <div className="bg-white rounded-lg border border-gray-100 p-6 space-y-4 my-4">
            {/* Main Entry Card */}
            <div className="flex items-start gap-4">
                {/* Patient Avatar */}
                <div className="w-12 h-12 bg-[#E8EEFD] rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-[#002FD4] font-bold text-lg">{avatarLetter}</span>
                </div>

                {/* Patient Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <h2 className="font-poppins text-lg font-semibold leading-7 text-[#0F1011] align-middle">{name}</h2>
                    </div>

                    <div className="flex items-center gap-6 flex-wrap">
                        <div className="flex items-center gap-2 mt-1">
                            <EnvelopeSimpleIcon size={20} color='#002FD4' />
                            <span className="font-poppins text-sm font-normal leading-5 capitalize text-[#0F1011]">
                                Email: {' ' + email}
                            </span>
                        </div>
                    </div>

                    <div className="mt-4">
                        <div className="grid grid-cols-3 gap-4">
                            <div className="space-y-2">
                                <label className="flex items-center gap-2">
                                    <Phone size={18} weight="duotone" className="text-[#002FD4]" />
                                    <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                                        Contact
                                    </span>
                                </label>
                                <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle ml-6">
                                    {contactNumber}
                                </div>
                            </div>

                            <div className="space-y-2">
                                <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                                    Emergency Contact
                                </span>
                                <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle mt-1">
                                    {emergencyContact}
                                </div>
                            </div>

                            <div className="space-y-2">
                                <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                                    Family Contact
                                </span>
                                <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle mt-1">
                                    {familyContact}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col justify-center gap-12 h-full">
                    <div
                    className='inline-flex items-center gap-1 w-fit px-2 rounded-full font-medium text-sm text-[#002FD4]'
                    >
                        <span>{age}Y{' '}|{' '}{gender}</span>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default SingleEntry