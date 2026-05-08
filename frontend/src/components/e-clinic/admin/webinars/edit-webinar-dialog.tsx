import { useState, useEffect, useMemo } from 'react'
import { CaretDownIcon, XIcon } from '@phosphor-icons/react'
import { Select } from '@mantine/core'
import { useUpdateAdminWebinar } from '@/hooks/use-admin-webinars'
import { useAdminDoctors } from '@/hooks/use-admin-doctors'
import { useAuth } from '@/context/auth/auth-context-utils'
import { toast } from 'react-toastify'
import Modal from '@/components/ui/modal'
import type { UpdateWebinarPayload } from '@/services/admin-webinar-service'

type WebinarType = 'free' | 'paid'

interface EditWebinarDialogProps {
    isOpen: boolean
    onClose: () => void
    webinar: {
        id: string
        title: string
        description: string
        webinar_date: string
        start_time: string
        end_time: string
        pricing_type: 'free' | 'paid'
        price: string
        participant_limit: number
        host_id: string
        visibility: 'public' | 'private'
        agenda: string
    } | null
}

export default function EditWebinarDialog({
    isOpen,
    onClose,
    webinar
}: EditWebinarDialogProps) {
    const [title, setTitle] = useState('')
    const [description, setDescription] = useState('')
    const [date, setDate] = useState('')
    const [startTime, setStartTime] = useState('')
    const [endTime, setEndTime] = useState('')
    const [selectedDoctor, setSelectedDoctor] = useState('')
    const [webinarType, setWebinarType] = useState<WebinarType>('free')
    const [price, setPrice] = useState('')
    const [participantLimit, setParticipantLimit] = useState('100')
    const [visibility, setVisibility] = useState<'public' | 'private'>('public')
    const [agenda, setAgenda] = useState('')
    const [isCustom, setIsCustom] = useState(false)

    const { mutate: updateWebinar, isPending } = useUpdateAdminWebinar()
    const { data: doctorsData, isLoading: isLoadingDoctors } = useAdminDoctors()
    const { user } = useAuth()

    // Sort doctors to show logged-in user first, or add them if not in list
    const sortedDoctors = useMemo(() => {
        const doctors = doctorsData || []
        if (!user?.id) return doctors

        const loggedInDoctor = doctors.find((d: any) => d.id === user.id)
        const otherDoctors = doctors.filter((d: any) => d.id !== user.id)

        // If logged-in user is in doctors list, put them first
        if (loggedInDoctor) {
            return [loggedInDoctor, ...otherDoctors]
        }

        // If logged-in user is NOT in doctors list (e.g., super_admin), add them manually
        if (user.id && user.name) {
            const currentUserAsDoctor = {
                id: user.id,
                name: user.name,
                email: user.email || ''
            }
            return [currentUserAsDoctor, ...doctors]
        }

        return doctors
    }, [doctorsData, user])

    // Format doctors for Mantine Select
    const doctorOptions = useMemo(() => {
        return sortedDoctors.map((doctor: any) => ({
            value: doctor.id,
            label: doctor.id === user?.id ? `${doctor.name} (You)` : doctor.name
        }))
    }, [sortedDoctors, user?.id])

    // Populate form with existing webinar data
    useEffect(() => {
        if (webinar && isOpen) {
            setTitle(webinar.title)
            setDescription(webinar.description)
            setDate(webinar.webinar_date)
            setStartTime(webinar.start_time)
            setEndTime(webinar.end_time)
            setSelectedDoctor(webinar.host_id)
            setWebinarType(webinar.pricing_type)
            setPrice(webinar.price)
            setParticipantLimit(String(webinar.participant_limit))
            setVisibility(webinar.visibility)
            setAgenda(webinar.agenda)
            const predefined = ['25', '50', '100', '150', '200']
    setIsCustom(!predefined.includes(String(webinar.participant_limit)))
        }
    }, [webinar, isOpen])

    if (!webinar) return null

    const handleSubmit = () => {
        if (!title || !description || !date || !startTime || !endTime || !selectedDoctor) {
            toast.error('Please fill in all required fields')
            return
        }

        // Block inverted time range
        if (endTime <= startTime) {
            toast.error('End time must be after start time')
            return
        }

        // Format time to HH:MM (remove seconds if present)
        const formatTime = (time: string) => {
            const parts = time.split(':')
            return `${parts[0]}:${parts[1]}`
        }

        // Guard numeric parsing — backend rejects 0 / NaN
        let priceValue = 0
        if (webinarType === 'paid') {
            const parsedPrice = parseFloat(price)
            if (!Number.isFinite(parsedPrice) || parsedPrice <= 0) {
                toast.error('Please enter a valid price greater than 0')
                return
            }
            priceValue = parsedPrice
        }

        const parsedLimit = parseInt(participantLimit, 10)
        if (!Number.isFinite(parsedLimit) || parsedLimit <= 0) {
            toast.error('Please enter a valid participant limit')
            return
        }

        const payload: UpdateWebinarPayload = {
            title,
            description,
            webinar_date: date,
            start_time: formatTime(startTime),
            end_time: formatTime(endTime),
            pricing_type: webinarType,
            price: priceValue,
            participant_limit: parsedLimit,
            host_id: selectedDoctor,
            visibility,
            agenda,
        }

        updateWebinar(
            { webinarId: webinar.id, payload },
            {
                onSuccess: () => {
                    toast.success('Webinar updated successfully!')
                    onClose()
                },
                onError: (error: any) => {
                    toast.error(error?.message || 'Failed to update webinar')
                }
            }
        )
    }

    const footer = (
        <>
            <button
                type="button"
                onClick={onClose}
                disabled={isPending}
                className="w-full px-8 py-3 rounded-md border border-gray-300 font-poppins font-semibold text-sm text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
                Cancel
            </button>
            <button
                type="button"
                onClick={handleSubmit}
                disabled={!title || !description || !date || !startTime || !endTime || !selectedDoctor || isPending}
                className="w-full px-8 py-3 rounded-md bg-[#002FD4] text-white font-poppins font-bold text-sm hover:bg-[#001FB8] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
                {isPending ? 'Updating...' : 'Update'}
            </button>
        </>
    )


    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Edit Webinar"
            footer={footer}
            maxWidth="2xl"
        >
            <div className="space-y-2">
                <div className='space-y-2'>
                    <div className="font-poppins font-normal text-sm leading-none text-[#0F1011]">Basic Details</div>
                    <input type="text" placeholder="Webinar Title" value={title} onChange={(e) => setTitle(e.target.value)}
                        className="text-[#6B7280] w-full px-4 py-3 mt-1 font-poppins font-normal text-xs leading-none rounded-md border border-[#E6E7EB] focus:outline-none focus:border-[#002FD4]" />
                    <textarea placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} rows={2}
                        className="text-[#6B7280] w-full px-4 py-3 mt-2 font-poppins font-normal text-xs leading-none rounded-md border border-[#E6E7EB] focus:outline-none focus:border-[#002FD4]" />
                </div>

                <div className="grid grid-cols-3 gap-4">
                    <div className="relative">
                        <label className="font-poppins font-normal text-xs text-[#0F1011] mb-1 block">Date</label>
                        <input type="date" placeholder='Date' value={date} onChange={(e) => setDate(e.target.value)}
                            className="text-[#6B7280] font-poppins font-semibold text-sm text-[#0F1011] align-middle w-full px-4 py-3 rounded-md border border-[#E6E7EB] focus:outline-none focus:border-[#002FD4]" />
                    </div>
                    <div className="relative">
                        <label className="font-poppins font-normal text-xs text-[#0F1011] mb-1 block">Start Time</label>
                        <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)}
                            className="text-[#6B7280] font-poppins font-semibold text-sm text-[#0F1011] align-middle w-full px-4 py-3 rounded-md border border-[#E6E7EB] focus:outline-none focus:border-[#002FD4]" />
                    </div>
                    <div className="relative">
                        <label className="font-poppins font-normal text-xs text-[#0F1011] mb-1 block">End Time</label>
                        <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)}
                            className="text-[#6B7280] font-poppins font-semibold text-sm text-[#0F1011] align-middle w-full px-4 py-3 rounded-md border border-[#E6E7EB] focus:outline-none focus:border-[#002FD4]" />
                    </div>
                </div>

                <div>
                    <div className="font-poppins font-normal text-sm leading-none text-[#0F1011] mb-4 mt-6">Host & Speakers</div>
                    <Select
                        value={selectedDoctor}
                        onChange={(value) => setSelectedDoctor(value || '')}
                        data={doctorOptions}
                        placeholder={isLoadingDoctors ? 'Loading healthcare providers...' : 'Choose Healthcare Provider'}
                        searchable
                        disabled={isLoadingDoctors}
                        nothingFoundMessage="No healthcare provider found"
                        maxDropdownHeight={300}
                        styles={{
                            input: {
                                fontFamily: 'Poppins',
                                fontSize: '14px',
                                padding: '12px 16px',
                                border: '1px solid #E6E7EB',
                                borderRadius: '6px',
                                color: '#6B7280',
                            },
                            dropdown: {
                                fontFamily: 'Poppins',
                                fontSize: '14px',
                            }
                        }}
                    />
                </div>

                <div className="max-w-[449px]">
                    <div className="font-poppins font-normal text-sm leading-none text-[#0F1011] mb-4 mt-6">Registration Fee</div>
                    <div className="flex items-center gap-3">
                        <input type="text" placeholder="Enter Amount" value={webinarType === 'paid' ? price : ''} onChange={(e) => setPrice(e.target.value)}
                            disabled={webinarType === 'free'}
                            className={`flex-1 px-4 py-3 rounded-md border text-[#6B7280] ${webinarType === 'free' ? 'bg-gray-50 text-gray-400' : 'border-gray-200 focus:border-[#002FD4]'} focus:outline-none font-poppins text-sm`} />
                        <span className="text-[#6B7280] font-medium font-poppins font-normal text-sm leading-none">Or</span>
                        <button onClick={() => setWebinarType(webinarType === 'free' ? 'paid' : 'free')}
                            className={`px-6 py-3 rounded-md font-poppins font-bold text-sm transition-all ${webinarType === 'free' ? 'bg-[#002FD4] text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>
                            Free
                        </button>
                    </div>
                </div>

                <div>
                    <div className="font-poppins font-normal text-sm leading-none text-[#0F1011] mb-4 mt-6">
                        Participant limit
                    </div>

                    <div className="relative">
                        {isCustom ? (
                            <div className="flex items-center gap-2">
                                <input
                                    type="number"
                                    min="1"
                                    max="1000"
                                    value={participantLimit}
                                    onChange={(e) => setParticipantLimit(e.target.value)}
                                    placeholder="Enter custom limit"
                                    className="w-full px-4 py-3 rounded-md border border-gray-200 focus:outline-none focus:border-[#002FD4] focus:ring-4 focus:ring-[#002FD4]/10 transition-all font-poppins text-sm text-[#0F1011] bg-white"
                                />

                                <button
                                    onClick={() => {
                                        setIsCustom(false)
                                        if (!participantLimit || isNaN(Number(participantLimit))) {
                                            setParticipantLimit("25")
                                        }
                                    }}
                                    className="p-3 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-600 transition-colors"
                                    title="Cancel custom"
                                >
                                    <XIcon size={18} weight="bold" />
                                </button>
                            </div>
                        ) : (
                            <select
                                value={participantLimit}
                                onChange={(e) => {
                                    const val = e.target.value
                                    if (val === "custom") {
                                        setIsCustom(true)
                                        setParticipantLimit("")
                                    } else {
                                        setParticipantLimit(val)
                                    }
                                }}
                                className="text-[#6B7280] appearance-none w-full px-4 py-3 rounded-md border border-gray-200 focus:outline-none focus:border-[#002FD4] focus:ring-4 focus:ring-[#002FD4]/10 transition-all font-poppins text-sm text-[#0F1011] bg-white cursor-pointer pr-10"
                            >
                                <option value="25">25</option>
                                <option value="50">50</option>
                                <option value="100">100</option>
                                <option value="150">150</option>
                                <option value="200">200</option>
                                <option value="custom">Custom</option>
                            </select>
                        )}

                        {!isCustom && (
                            <CaretDownIcon
                                size={18}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none"
                                weight="bold"
                            />
                        )}
                    </div>
                </div>

                {/* <div>
                            <div className="font-poppins font-normal text-sm leading-none text-[#0F1011] mb-4 mt-6">
                                Status
                            </div>
                            <div className="relative">
                                <select
                                    value={status}
                                    onChange={(e) => setStatus(e.target.value as any)}
                                    className="text-[#6B7280] appearance-none w-full px-4 py-3 rounded-md border border-gray-200 focus:outline-none focus:border-[#002FD4] focus:ring-4 focus:ring-[#002FD4]/10 transition-all font-poppins text-sm text-[#0F1011] bg-white cursor-pointer pr-10"
                                >
                                    <option value="draft">Draft</option>
                                    <option value="scheduled">Scheduled</option>
                                    <option value="live">Live</option>
                                    <option value="completed">Completed</option>
                                    <option value="cancelled">Cancelled</option>
                                </select>

                                <CaretDownIcon
                                    size={18}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none"
                                    weight="bold"
                                />
                            </div>
                        </div> */}
            </div>
        </Modal>
    )
}

