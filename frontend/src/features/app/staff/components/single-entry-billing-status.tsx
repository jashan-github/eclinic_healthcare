
import { useState } from 'react'
import { Phone, EnvelopeSimple, UserIcon, FileTextIcon } from '@phosphor-icons/react'
import { Modal } from '@mantine/core'
import { useDownloadStaffInvoice } from '@/hooks/use-staff'
import { toast } from 'react-toastify'
import { formatFee } from '@/utils/helper'

interface SingleEntryProps {
    invoiceId: string
    name: string
    email: string
    paymentMethod?: 'Online' | 'Cash'
    amount: number
    currency: string
    paymentDate: string
    contactNumber: string
    emergencyContact: string
    familyContact: string
}

const SingleEntry: React.FC<SingleEntryProps> = ({
    invoiceId,
    name,
    email,
    paymentMethod,
    paymentDate,
    amount,
    currency,
    contactNumber,
    emergencyContact,
    familyContact,
}) => {
    const [isContactOpen, setIsContactOpen] = useState(false)
    const downloadMutation = useDownloadStaffInvoice()

    const handleDownloadInvoice = () => {
        downloadMutation.mutate(invoiceId, {
            onSuccess: () => {
                toast.success('Invoice downloaded successfully')
            },
            onError: (error: any) => {
                toast.error(error?.message || 'Failed to download invoice')
            }
        })
    }

    return (
        <div className="bg-white rounded-lg border border-gray-100 p-6 space-y-4 my-4">
            {/* Main Entry Card */}
            <div className="flex items-start gap-4">
                {/* Patient Avatar */}
                <FileTextIcon size={30} color='#002FD4' />

                {/* Patient Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <h2 className="font-poppins text-lg font-semibold leading-7 text-[#0F1011] align-middle">{name}</h2>
                    </div>
                    <div className="flex items-center gap-6 flex-wrap">
                        <div className="flex items-center gap-2">
                            <span className="font-poppins text-sm font-normal leading-5 capitalize text-[#0F1011]">
                                Payment on {' ' + paymentDate}
                            </span>
                        </div>

                        <div className="flex items-center gap-2 font-poppins text-sm">
                            Paid
                            <span className="font-poppins text-sm font-bold leading-5 capitalize text-[#0F1011]">
                                {formatFee(amount, currency)}
                            </span>
                        </div>
                    </div>

                    <div className="flex items-center gap-6 mt-2">
                        <span className="font-poppins text-sm font-semibold leading-5 text-[#0F1011] align-middle">
                            Payment Mode:{' '}{paymentMethod}
                        </span>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col justify-end h-full pt-14 gap-2">
                    {/* <div
                        onClick={() => setIsContactOpen(true)}
                        className="w-full cursor-pointer transition-colors"
                    >
                        <span className="font-poppins text-sm font-medium leading-5 text-center block underline text-slate-600">
                            View Contact
                        </span>
                    </div> */}
                    <div
                        onClick={() => !downloadMutation.isPending && handleDownloadInvoice()}
                        className={`w-full transition-colors ${downloadMutation.isPending ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                        <span className={`font-poppins text-sm font-medium leading-5 text-center block underline text-slate-600`}>
                            {downloadMutation.isPending ? 'Downloading...' : 'Download Invoice'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Contact Details Modal */}
            <Modal
                opened={isContactOpen}
                onClose={() => setIsContactOpen(false)}
                title={
                    <div className="flex items-center justify-between w-full">
                        <span className="font-poppins text-base font-bold leading-6 text-[#0F1011]">Patient Contact Details</span>
                    </div>
                }
                size="580px"
                radius={'lg'}
                centered
                styles={{
                    header: {
                        borderBottom: 'none',
                        paddingBottom: 0,
                        paddingLeft: '2rem',
                        paddingRight: '2rem'
                    },
                    body: {
                        paddingTop: 0
                    }
                }}
            >
                <div className="p-6 space-y-6">
                    {/* Full Name and Email Row */}
                    <div className="grid grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="flex items-center gap-2">
                                <UserIcon size={18} className="text-[#002FD4]" />
                                <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                                    Full Name
                                </span>
                            </label>
                            <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle ml-6">
                                {name}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="flex items-center gap-2">
                                <EnvelopeSimple size={18} weight="duotone" className="text-[#002FD4]" />
                                <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                                    Email
                                </span>
                            </label>
                            <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle ml-6">
                                {email}
                            </div>
                        </div>
                    </div>

                    {/* Contact Numbers Row - All in One Box */}
                    <div className="border border-gray-200 rounded-lg p-4">
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
            </Modal>
        </div>
    )
}

export default SingleEntry