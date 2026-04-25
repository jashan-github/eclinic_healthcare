// src/components/settings/AppointmentSettings.tsx
import { Button, Select, Stack } from '@mantine/core'
import { useState, useEffect } from 'react'
import { useAdminSettings, useUpdateAdminSettings } from '@/hooks/use-admin-settings'

const AppointmentSettings = () => {
    const { data: settingsData, isLoading } = useAdminSettings()
    const { mutate: updateSettings, isPending } = useUpdateAdminSettings()

    const [autoConfirm, setAutoConfirm] = useState(true)
    const [sameDayBooking, setSameDayBooking] = useState(true)
    const [bookingWindow, setBookingWindow] = useState('30')

    // Load settings from API
    useEffect(() => {
        if (settingsData?.data) {
            const settings = settingsData.data
            setAutoConfirm(settings.auto_approve_appointments)
            setSameDayBooking(settings.allow_same_day_booking)
            setBookingWindow(String(settings.booking_window_days))
        }
    }, [settingsData])

    const handleSave = () => {
        updateSettings({
            auto_approve_appointments: autoConfirm,
            allow_same_day_booking: sameDayBooking,
            booking_window_days: parseInt(bookingWindow),
        })
    }

    if (isLoading) {
        return (
            <div className="py-12 px-6 bg-white mt-10 rounded-lg">
                <div className="flex justify-center items-center h-40">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#002FD4]"></div>
                </div>
            </div>
        )
    }

    return (
        <div className="py-12 px-6 bg-white mt-10 rounded-lg">
            <div>
                {/* Header */}
                <div className="mb-10">
                    <div className='font-poppins font-semibold text-xl leading-6 text-[#0F1011]'>
                        Appointment Settings
                    </div>
                    <div className="mt-1 font-poppins font-normal text-sm leading-5 text-[#64748B]">
                        Configure appointment booking rules
                    </div>
                </div>

                <Stack gap="xl">
                    {/* Auto-confirm appointments */}
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="font-poppins font-semibold text-sm leading-none text-[#0F1011]">
                                Auto-confirm appointments
                            </div>
                            <div className="mt-1 font-poppins font-normal text-sm leading-5 text-[#627084]">
                                If enabled, appointment requests are automatically approved without doctor action
                            </div>
                        </div>

                        {/* Custom Switch */}
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                checked={autoConfirm}
                                onChange={(e) => setAutoConfirm(e.target.checked)}
                                className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none rounded-full peer 
                                after:content-[''] after:absolute after:top-[2px] after:left-[2px] 
                                after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all
                                peer-checked:bg-[#002FD4] peer-checked:after:translate-x-full">
                            </div>
                        </label>
                    </div>

                    {/* Allow same-day bookings */}
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="font-poppins font-semibold text-sm leading-none text-[#0F1011]">
                                Allow same-day bookings
                            </div>
                            <div className="mt-1 font-poppins font-normal text-sm leading-5 text-[#627084]">
                                If enabled, patients can book appointments for the same day
                            </div>
                        </div>

                        {/* Custom Switch */}
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                checked={sameDayBooking}
                                onChange={(e) => setSameDayBooking(e.target.checked)}
                                className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none rounded-full peer 
                                after:content-[''] after:absolute after:top-[2px] after:left-[2px] 
                                after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all
                                peer-checked:bg-[#002FD4] peer-checked:after:translate-x-full">
                            </div>
                        </label>
                    </div>

                    {/* Booking window */}
                    <div>
                        <div className="mb-2 font-poppins font-semibold text-sm leading-none text-[#0F1011]">
                            Booking window (days in advance)
                        </div>
                        <div className="mb-2 font-poppins font-normal text-sm leading-5 text-[#627084]">
                            Maximum number of days in advance patients can book (must be ≥ 1)
                        </div>
                        <Select
                            value={bookingWindow}
                            onChange={(value) => setBookingWindow(value || '30')}
                            data={[
                                { value: '7', label: '7 days' },
                                { value: '14', label: '14 days' },
                                { value: '21', label: '21 days' },
                                { value: '30', label: '30 days' },
                                { value: '60', label: '60 days' },
                                { value: '90', label: '90 days' },
                                { value: '180', label: '180 days' },
                                { value: '365', label: '1 year' },
                            ]}
                            placeholder="Select booking window"
                            className="w-full"
                            styles={{
                                input: {
                                    height: 48,
                                    borderRadius: 12,
                                    fontSize: 16,
                                },
                            }}
                        />
                    </div>

                    {/* Save Button */}
                    <div className="pt-6 border-t border-gray-200">
                        <Button
                            onClick={handleSave}
                            className="text-white font-medium px-8 py-3 rounded-lg shadow-md transition"
                            style={{ background: '#002FD4' }}
                            radius={8}
                            loading={isPending}
                            disabled={isPending}
                        >
                            <span className='font-poppins font-semibold text-sm leading-5 text-center'>
                                {isPending ? 'Saving...' : 'Save Changes'}
                            </span>
                        </Button>
                    </div>
                </Stack>
            </div>
        </div>
    )
}

export default AppointmentSettings