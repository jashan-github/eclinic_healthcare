import { Check, UserIcon, CalendarBlankIcon, MapPinIcon, VideoCameraIcon, XCircleIcon } from '@phosphor-icons/react'
import { type FC } from 'react'

interface RequestsCardProps {
    name: string
    gender: string
    age: number
    reason: string
    description?: string
    submittedAt: string
    timeAsked: string
    inclinic: boolean
    onApprove?: () => void
    onDecline?: () => void
    isPending: boolean
}

const formatDateTime = (value: string, withAt = false) => {
    const date = new Date(value);

    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = date.getFullYear();
    const formattedDate = `${month}-${day}-${year}`;

    const time = date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
    });

    return withAt
        ? `${formattedDate} at ${time}`
        : `${formattedDate} ${time}`;
}

const RequestsCard: FC<RequestsCardProps> = ({
    name,
    gender,
    age,
    reason,
    description = 'No Description Available',
    submittedAt,
    timeAsked,
    inclinic = false,
    onApprove,
    onDecline,
    isPending
}) => {
    return (
        <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="py-4">
                <div className="flex items-stretch gap-6 px-6">

                    <div className="flex-shrink-0">
                        <div className="w-12 h-12 rounded-full bg-pink-100 flex items-center justify-center text-pink-600 font-semibold text-lg">
                            <UserIcon />
                        </div>
                    </div>

                    <div className="flex-1">
                        <div className='space-y-2'>
                            <div className="font-poppins font-semibold text-base text-[#0F1011]">
                                {name} | {gender} | {age}Y
                            </div>
                            <div className="font2-poppins font-normal text-sm leading-5 text-[#0F1011]">{reason}</div>
                            <div className="font-poppins font-normal text-sm leading-5 text-[#64748B]">
                                {description}
                            </div>
                            <div className="font-poppins font-normal text-sm leading-5 text-[#64748B] mt-4 flex items-center gap-6">
                                <span className="flex items-center gap-1">
                                    <CalendarBlankIcon size={16} weight="regular" className="text-[#64748B]" />
                                    <span>{formatDateTime(timeAsked, true)}</span>
                                </span>
                                <span className="flex items-center gap-2">
                                    Submitted: {formatDateTime(submittedAt)}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col justify-between min-w-fit">

                        {inclinic ? (
                            <div className="flex justify-end">
                                <div
                                    className="inline-flex gap-2 items-center justify-center gap-1.5 w-[103px] h-8 px-[9px] py-2 rounded-md border border-[#E8E8E8] bg-white"
                                    style={{
                                        paddingTop: '8px',
                                        paddingBottom: '8px',
                                        paddingLeft: '9px',
                                        paddingRight: '9px',
                                    }}
                                >
                                    <MapPinIcon size={16} color="#002FD4" className="flex-shrink-0" />
                                    <div
                                        className="font-poppins font-normal text-[13px] leading-[18px] text-[#0F1011] capitalize"
                                        style={{ lineHeight: '18px' }}
                                    >
                                        In-clinic
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex justify-end">
                                <div
                                    className="inline-flex gap-2 items-center justify-center gap-1.5 w-[156px] h-8 px-[9px] py-2 rounded-md border border-[#E8E8E8] bg-white"
                                    style={{
                                        paddingTop: '8px',
                                        paddingBottom: '8px',
                                        paddingLeft: '9px',
                                        paddingRight: '9px',
                                    }}
                                >
                                    <VideoCameraIcon size={16} color="#002FD4" className="flex-shrink-0" />
                                    <div
                                        className="font-poppins font-normal text-[13px] leading-[18px] text-[#0F1011] capitalize"
                                        style={{ lineHeight: '18px' }}
                                    >
                                        Teleconsultation
                                    </div>
                                </div>
                            </div>
                        )}

                        {isPending && <div className="flex gap-3 justify-end">
                            <button
                                onClick={onApprove}
                                className="flex items-center w-[113px] h-8 rounded-md px-3 py-[7.5px] bg-[#002FD4] opacity-100 gap-2 text-white hover:cursor-pointer"
                            >
                                <Check size={18} weight="bold" />
                                <span className="font-poppins font-semibold text-sm leading-5 text-center align-middle">
                                    Approve
                                </span>
                            </button>
                            <button
                                onClick={onDecline}
                                className="w-[107px] h-8 rounded-md border border-[#E2E8F0] bg-white px-[13px] pt-[7.5px] pb-[8.5px] flex items-center gap-2 text-[#DC2626] hover:cursor-pointer"
                            >
                                <XCircleIcon size={18} weight="bold" />
                                <span className="font-poppins font-semibold text-sm leading-5 text-center">
                                    Decline
                                </span>
                            </button>
                        </div>}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default RequestsCard
