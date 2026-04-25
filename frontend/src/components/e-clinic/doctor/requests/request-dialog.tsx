import { XIcon, CalendarBlankIcon } from '@phosphor-icons/react'
import { type FC, useState } from 'react'

interface RequestDialogProps {
    open: boolean
    requestId: string
    patientName: string
    reason: string
    requestedTime: string  // ISO string like "2026-01-08T14:30:00"
    submittedAt: string    // ISO string
    mode: 'approve' | 'decline'
    waiverDoctorDecides?: boolean
    waiverChoices?: number[]
    onClose: () => void
    onApprove?: (waiverPercent: number) => void
    onDecline?: (reason: string) => void
}

// Same formatting function as in RequestsCard
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

const RequestDialog: FC<RequestDialogProps> = ({
    open,
    patientName,
    reason,
    requestedTime,
    submittedAt,
    mode,
    waiverDoctorDecides = false,
    waiverChoices = [0, 25, 50, 75, 100],
    onClose,
    onApprove,
    onDecline
}) => {
    const [declineReason, setDeclineReason] = useState('')
    const [selectedWaiverPercent, setSelectedWaiverPercent] = useState<number>(0)

    if (!open) return null

    const handleAction = () => {
        if (mode === 'approve' && onApprove) {
            onApprove(selectedWaiverPercent)
        } else if (mode === 'decline' && onDecline && declineReason.trim()) {
            onDecline(declineReason.trim())
        }
    }

    return (
        <>
            <div className="fixed inset-0 bg-black/40 z-50" onClick={onClose} />

            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                <div className="bg-white rounded-xl shadow-2xl md:max-w-[70%] w-full">
                    <div className="flex items-center justify-between px-6 pt-6">
                        <div className="font-poppins font-bold text-base leading-6 text-[#0F1011]">
                            Appointment Request
                        </div>
                        <button onClick={onClose} className="hover:text-gray-600 hover:cursor-pointer">
                            <XIcon size={24} weight="bold" />
                        </button>
                    </div>

                    <div className="px-6 py-5 space-y-5">
                        <div className="space-y-2">
                            <div className="font-poppins font-semibold text-sm leading-6 text-[#0F1011]">
                                From: {patientName}
                            </div>
                            <div className="font-poppins font-normal text-sm leading-5 text-[#0F1011]">
                                Reason: {reason}
                            </div>
                        </div>

                        {/* Updated with same MM-DD-YYYY formatting */}
                        <div className="flex flex-wrap gap-x-8 gap-y-2 text-sm text-[#64748B] font-poppins">
                            <span className="flex items-center gap-2">
                                <CalendarBlankIcon size={16} weight="fill" />
                                {formatDateTime(requestedTime, true)}  {/* e.g., 01-08-2026 at 02:30 PM */}
                            </span>
                            <span>Submitted {formatDateTime(submittedAt)}  {/* e.g., 01-08-2026 01:45 PM */}</span>
                        </div>

                        {mode === 'approve' && waiverDoctorDecides && (
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="font-poppins font-normal text-sm text-[#0F1011]">
                                        Waiver percentage
                                    </label>
                                    <span className="font-poppins font-semibold text-sm text-[#002FD4]">
                                        {selectedWaiverPercent}%
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min={0}
                                    max={waiverChoices.length - 1}
                                    step={1}
                                    value={waiverChoices.indexOf(selectedWaiverPercent) === -1 ? 0 : waiverChoices.indexOf(selectedWaiverPercent)}
                                    onChange={(e) => setSelectedWaiverPercent(waiverChoices[Number(e.target.value)])}
                                    className="w-full accent-[#002FD4]"
                                />
                                <div className="flex justify-between mt-1">
                                    {waiverChoices.map((pct) => (
                                        <span key={pct} className="font-poppins text-xs text-[#64748B]">{pct}%</span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {mode === 'decline' && (
                            <div>
                                <label className="font-poppins font-normal text-sm leading-none text-[#0F1011]">
                                    Reason for declining
                                </label>
                                <textarea
                                    value={declineReason}
                                    onChange={(e) => setDeclineReason(e.target.value)}
                                    rows={3}
                                    placeholder="Type reason here..."
                                    className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#002FD4] font-poppins text-sm resize-none mt-1"
                                />
                            </div>
                        )}

                        <div className="inline-flex gap-8 pt-3 w-full">
                            <button
                                onClick={handleAction}
                                disabled={mode === 'decline' && !declineReason.trim()}
                                className={`w-full py-2 ${mode === 'approve' ? 'bg-[#002FD4]' : 'bg-red-600'
                                    } text-white font-poppins font-medium text-sm rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors`}
                            >
                                <span className="font-poppins font-semibold text-sm leading-5 text-center w-full">
                                    {mode === 'approve' ? 'Approve' : 'Decline'}
                                </span>
                            </button>
                            <button
                                onClick={onClose}
                                className="w-full py-2 font-poppins text-sm font-medium text-[#0F1011] hover:bg-gray-100 rounded-md transition-colors border border-[#E1E7EF] bg-[#F9FAFB]"
                            >
                                <span className="font-poppins font-semibold text-sm leading-5 text-center text-[#0F1011]">
                                    Cancel
                                </span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}

export default RequestDialog