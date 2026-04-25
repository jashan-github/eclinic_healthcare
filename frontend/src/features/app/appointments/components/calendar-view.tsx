import { useMemo, useState } from 'react'
import { DatePicker, DatesProvider } from '@mantine/dates'
import { format, addMinutes, startOfDay } from 'date-fns'
import { CalendarBlankIcon, CaretDoubleLeftIcon, CaretDoubleRightIcon, CaretDownIcon } from '@phosphor-icons/react'
import { Switch } from '@mantine/core'
import { useDoctorAppointments } from '@/hooks/use-appointment'

const CalendarView = () => {
    const [selectedDate, setSelectedDate] = useState<Date | null>(new Date())
    const [slotDuration, setSlotDuration] = useState(10)
    const [sidebarOpen, setSidebarOpen] = useState(true)

    const { data: appointmentsData } = useDoctorAppointments()
    console.log("appointmentsData", appointmentsData)

    const appointments = useMemo(() => {
        if (!selectedDate || !appointmentsData) return []

        const selectedDateStr = format(selectedDate, 'yyyy-MM-dd')

        // Combine all appointments from today, upcoming, and completed
        const allAppointments = [
            ...(appointmentsData.today?.data || []),
            ...(appointmentsData.upcoming?.data || []),
            ...(appointmentsData.completed?.data || []),
        ]

        // Filter appointments for the selected date
        return allAppointments
            .filter((apt) => apt.appointment_date === selectedDateStr)
            .map((apt) => {
                const time24 = apt.start_time.slice(0, 5) // "11:00:00" → "11:00"
                const time12 = apt.start_time // Already in "11:00 AM" format

                // Choose a color based on consultation type or status
                let color = 'bg-blue-500'
                if (apt.consultation_mode === 'TELECONSULTATION') {
                    color = 'bg-purple-500'
                } else if (apt.status === 'CONFIRMED') {
                    color = 'bg-green-500'
                } else if (apt.status === 'PENDING') {
                    color = 'bg-orange-500'
                }

                return {
                    time: time24,
                    displayTime: time12,
                    name: apt.patient_name,
                    color,
                    consultationType: apt.consultation_mode,
                    status: apt.status,
                }
            })
    }, [selectedDate, appointmentsData])

    const durations = [2, 3, 5, 10, 15, 20, 30]

    const timeSlots = useMemo(() => {
        if (!slotDuration) return []
        const start = startOfDay(new Date())
        const slots = []
        for (let i = 0; i < 24 * 60; i += slotDuration) {
            const time = addMinutes(start, i)
            const formatted = format(time, 'h:mm a').replace(':00', '')
            slots.push(formatted)
        }
        return slots
    }, [slotDuration])

    const formatTimeForComparison = (time12: string) => {
        const [time, period] = time12.split(' ')
        let [hours, minutes] = time.split(':')
        let h = parseInt(hours)
        if (period === 'PM' && h !== 12) h += 12
        if (period === 'AM' && h === 12) h = 0
        return `${h.toString().padStart(2, '0')}:${minutes || '00'}`
    }

    const selectedDayName = selectedDate ? format(selectedDate, 'EEEE') : 'Select Day'

    return (
        <div className="flex h-screen bg-gray-50">
            <div className={`relative flex transition-all duration-300 ease-in-out bg-white border-r border-gray-200 ${sidebarOpen ? 'w-96' : 'w-0'
                }`}>
                <div className={`overflow-hidden transition-opacity duration-300 ${sidebarOpen ? 'w-96 opacity-100' : 'w-0 opacity-0'}`}>
                    <div className=" h-full">
                        <div className="mb-6">
                            <div className="p-4 text-lg font-semibold text-gray-800 mb-4 flex flex-row justify-between items-center">
                                <span className="font-poppins font-bold text-sm leading-5 text-[#0F1011]">
                                    {selectedDate
                                        ? format(selectedDate, 'EEEE, MMMM d, yyyy')
                                        : 'Select a date'}
                                </span>
                                <CaretDownIcon weight='bold' />
                            </div>

                            <DatesProvider settings={{ consistentWeeks: true }}>
                                <DatePicker
                                    type="default"
                                    value={selectedDate}
                                    onChange={(value) => setSelectedDate(value as Date | null)}
                                    size="lg"
                                    styles={{
                                        day: {
                                            '&[data-selected]': {
                                                backgroundColor: '#002FD4',
                                                color: 'white',
                                                fontWeight: 600,
                                            },
                                        },
                                    }}

                                />
                            </DatesProvider>

                            <div className="mt-1 p-4 flex items-center justify-between border-y border-gray-200">
                                <span className="font-poppins font-normal text-sm leading-6 text-[#0F1011]">Free slots only</span>
                                <Switch
                                    color="blue"
                                    size="md"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className={`
                        absolute top-1/4 z-50
                        p-2 bg-white border border-gray-300
                        flex items-center justify-center shadow-lg hover:bg-gray-50
                        transition-all duration-300
                        ${sidebarOpen
                            ? '-right-5'
                            : '-right-5'
                        }
                    `}
                >
                    {sidebarOpen ? (
                        <CaretDoubleLeftIcon />
                    ) : (
                        <CaretDoubleRightIcon />
                    )}
                </button>

                {!sidebarOpen && (
                    <div className="w-1 bg-gray-200 absolute left-0 top-0 bottom-0" />
                )}
            </div>

            <div className="flex-1 overflow-y-auto bg-white p-8">
                <div className="mb-6">
                    <div className="flex items-center gap-4 justify-end">
                        <span className="font-poppins font-bold text-sm text-[#0F1011]">
                            Slot duration:
                        </span>

                        <div className="inline-flex items-center border border-gray-200 rounded-md overflow-hidden">
                            {durations.map((min, index) => (
                                <button
                                    key={min}
                                    onClick={() => setSlotDuration(min)}
                                    className={`relative px-4 h-9 font-poppins font-normal text-sm leading-[30px] min-w-[64px] flex items-center justify-center transition-all duration-200 ${index !== 0 ? 'border-l border-gray-200' : ''
                                        } ${slotDuration === min
                                            ? 'bg-[#002FD4] text-white'
                                            : 'text-[#0F1011] hover:bg-gray-100'
                                        }`}
                                >
                                    <span className="relative z-10">
                                        {min} mins
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="w-full border border-gray-300 rounded-t-lg overflow-hidden">

                    <div className="border-b border-gray-300 py-4 text-center relative">
                        <div className="font-poppins font-bold text-[13px] leading-6 text-center text-[#002FD4]">
                            {selectedDayName}
                        </div>
                        <div className="absolute inset-y-0 left-[90.6px] w-px bg-gray-300" />
                    </div>

                    {timeSlots.map((time) => {
                        const time24 = formatTimeForComparison(time)
                        const appointment = appointments.find((apt) => apt.time === time24)
                        const displayTime = time.includes(':') ? time : `${time.replace(' ', ':00 ')}`

                        return (
                            <div key={time} className="flex h-10 relative">
                                <div className="w-23 flex items-center justify-end pr-4 font-poppins font-bold text-[12px] leading-6 text-right text-[#767676] text-gray-500 border-r border-gray-300">
                                    {displayTime}
                                </div>

                                <div className="flex-1 relative border-r border-gray-300">
                                    <div className="border-t border-gray-200 absolute inset-x-0 top-1/2 -translate-y-1/2" />

                                    {appointment && (
                                        <div className="absolute left-6 top-1/2 -translate-y-1/2">
                                            <span
                                                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-white font-poppins font-bold text-[10px] leading-6 ${appointment.color}`}
                                            >
                                                <CalendarBlankIcon size={14} weight="fill" />
                                                <span className="truncate max-w-48">
                                                    {appointment.name}
                                                    {appointment.consultationType === 'TELECONSULTATION' && ' (Online)'}
                                                </span>
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}

export default CalendarView
