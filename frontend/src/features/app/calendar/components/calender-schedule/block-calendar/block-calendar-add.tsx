import type { TimeOffPayload } from '@/types/calendar'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button, Checkbox, Flex, Stack, Textarea } from '@mantine/core'
import { DatePicker } from '@mantine/dates'
import { type FC, type ReactElement } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { useBlockCalendarSlots } from '../../../hooks/use-block-calendar-slots'
import { ArrowLeftIcon } from '@phosphor-icons/react'
import { useAuth } from '@/context/auth/auth-context-utils'
import BaseTimePicker from '@/components/form/BaseTimePicker'

// Zod schema with time slots
const calendarBlockSchema = z.object({
  dates: z.tuple([z.string().nullable(), z.string().nullable()]),
  isFullDay: z.boolean(),
  startTime: z.string().nullable().optional(),
  endTime: z.string().nullable().optional(),
  reason: z.string().max(500, 'Reason must be 500 characters or fewer').optional()
}).refine((data) => {
  // If not full day, both start and end times are required
  if (!data.isFullDay) {
    return !!data.startTime && !!data.endTime
  }
  return true
}, {
  message: 'Please select both start and end times',
  path: ['startTime']
})

export type CalendarBlockForm = z.infer<typeof calendarBlockSchema>

interface BlockCalendarAddProps {
  isOpen: boolean
  setIsOpen: (isOpen: boolean) => void
}

const BlockCalendarAdd: FC<BlockCalendarAddProps> = ({
  isOpen,
  setIsOpen
}): ReactElement => {
  const { saveBlockCalendarSlots, isSaving } = useBlockCalendarSlots()
  const { user } = useAuth()

  const { control, handleSubmit, reset, watch, formState: { errors } } =
    useForm<CalendarBlockForm>({
      resolver: zodResolver(calendarBlockSchema),
      defaultValues: {
        dates: [null, null],
        isFullDay: false,
        startTime: null,
        endTime: null,
        reason: ''
      }
    })

  const isFullDay = watch('isFullDay')

  const onSubmit = async (data: CalendarBlockForm) => {
    if (!data.dates[0]) {
      toast.error('Please select a date')
      return
    }

    if (!user?.clinic_id) {
      toast.error('Clinic ID is required')
      return
    }

    // Parse date strings (YYYY-MM-DD format) and normalize to start of day in local timezone
    const parseDateString = (dateStr: string): Date => {
      // If date string is in YYYY-MM-DD format, parse it properly
      const date = new Date(dateStr)
      // Normalize to start of day in local timezone to avoid timezone issues
      date.setHours(0, 0, 0, 0)
      return date
    }
    
    const startDate = parseDateString(data.dates[0])
    // If no end date selected, use start date as end date (single day selection)
    const endDate = data.dates[1] ? parseDateString(data.dates[1]) : startDate
    
    // Use full day times (00:00 to 23:59) if full day is selected, otherwise use selected times
    const startTime = data.isFullDay ? '00:00' : (data.startTime || '00:00')
    const endTime = data.isFullDay ? '23:59' : (data.endTime || '23:59')

    // Parse time strings without using split
    const parseTimeString = (timeStr: string): { hours: number; minutes: number } => {
      const colonIndex = timeStr.indexOf(':')
      if (colonIndex === -1) {
        return { hours: 0, minutes: 0 } // Default fallback
      }
      const hours = parseInt(timeStr.substring(0, colonIndex), 10)
      const minutes = parseInt(timeStr.substring(colonIndex + 1), 10)
      return {
        hours: isNaN(hours) ? 0 : hours,
        minutes: isNaN(minutes) ? 0 : minutes
      }
    }
    
    const startTimeParts = parseTimeString(startTime)
    const endTimeParts = parseTimeString(endTime)

    // Create single time-off entry with date range
    try {
      // Get start date components
      const startYear = startDate.getFullYear()
      const startMonth = String(startDate.getMonth() + 1).padStart(2, '0')
      const startDay = String(startDate.getDate()).padStart(2, '0')
      
      // Get end date components
      const endYear = endDate.getFullYear()
      const endMonth = String(endDate.getMonth() + 1).padStart(2, '0')
      const endDay = String(endDate.getDate()).padStart(2, '0')
      
      // Format time for ISO string (HH:MM:SS)
      const startTimeFormatted = data.isFullDay 
        ? '00:00:00' 
        : `${startTimeParts.hours.toString().padStart(2, '0')}:${startTimeParts.minutes.toString().padStart(2, '0')}:00`
      const endTimeFormatted = data.isFullDay
        ? '23:59:59'
        : `${endTimeParts.hours.toString().padStart(2, '0')}:${endTimeParts.minutes.toString().padStart(2, '0')}:00`
      
      // Construct ISO strings: start date with start time, end date with end time
      const startISO = `${startYear}-${startMonth}-${startDay}T${startTimeFormatted}.000Z`
      const endISO = `${endYear}-${endMonth}-${endDay}T${endTimeFormatted}.999Z`

      const payload: TimeOffPayload = {
        clinic_id: user.clinic_id,
        start_datetime: startISO,
        end_datetime: endISO,
        reason: data.reason?.trim() || ''
      }

      await new Promise<void>((resolve, reject) => {
        saveBlockCalendarSlots(payload, {
          onSuccess: () => resolve(),
          onError: (error) => reject(error)
        })
      })
      
      reset()
      setIsOpen(false)
    } catch (error) {
      // Error handling is done in the mutation's onError callback
      console.error('Error creating time-off entry:', error)
    }
  }

  if (!isOpen) return <></>

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/30 bg-opacity-10 transition-opacity"
        onClick={() => setIsOpen(false)}
      />

      {/* Drawer Panel */}
      <div
        className="relative bg-white w-full max-w-md h-full shadow-2xl flex flex-col animate-in slide-in-from-right"
        style={{ animationDuration: '300ms' }}
      >
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <button
            onClick={() => setIsOpen(false)}
            className="flex flex-row items-center gap-2 hover:cursor-pointer"
          >
            <ArrowLeftIcon weight="bold" />
            <span className="font-poppins font-bold text-base leading-6 text-[#0F1011]">Block Calendar</span>
          </button>
        </div>

        {/* Body - Scrollable */}
        <div className="flex-1 overflow-y-auto">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <Stack gap={10}>
              {/* Calendar */}
              <Controller
                name="dates"
                control={control}
                render={({ field }) => {
                  // Convert string dates (YYYY-MM-DD) to Date objects for DatePicker
                  const dateValue: [Date | null, Date | null] = [
                    field.value[0] ? (() => {
                      const date = new Date(field.value[0])
                      // Normalize to avoid timezone issues
                      date.setHours(0, 0, 0, 0)
                      return date
                    })() : null,
                    field.value[1] ? (() => {
                      const date = new Date(field.value[1])
                      // Normalize to avoid timezone issues
                      date.setHours(0, 0, 0, 0)
                      return date
                    })() : null
                  ]

                  // Get today's date at start of day for comparison
                  const today = new Date()
                  today.setHours(0, 0, 0, 0)

                  return (
                    <DatePicker
                      type="range"
                      allowSingleDateInRange={true}
                      value={dateValue}
                      minDate={today}
                      onChange={(value) => {
                        if (!value) {
                          field.onChange([null, null])
                          return
                        }

                        const [startDate, endDate] = value

                        // Helper to convert Date to YYYY-MM-DD string (normalized to avoid timezone issues)
                        const toDateString = (date: Date | string | null): string | null => {
                          if (!date) return null
                          if (typeof date === 'string') {
                            // If already a string, check if it's ISO format and extract date part
                            if (date.includes('T')) {
                              return date.split('T')[0]
                            }
                            return date
                          }
                          if (date instanceof Date) {
                            // Normalize to local date string (YYYY-MM-DD) to avoid timezone issues
                            const year = date.getFullYear()
                            const month = String(date.getMonth() + 1).padStart(2, '0')
                            const day = String(date.getDate()).padStart(2, '0')
                            return `${year}-${month}-${day}`
                          }
                          return null
                        }

                        // Convert both dates to strings
                        const startStr = toDateString(startDate)
                        const endStr = toDateString(endDate)

                        // Update the field with whatever the user selected
                        // If only start is selected, endStr will be null (allowing range selection to continue)
                        // If both are selected, both will have values
                        field.onChange([startStr, endStr])
                      }}
                      size="xl"
                    />
                  )
                }}
              />

              {/* Entire Day Checkbox */}
              <div className="px-6 py-4">
                <Controller
                  name="isFullDay"
                  control={control}
                  render={({ field }) => (
                    <div className="flex items-center justify-between w-full">
                      <label 
                        htmlFor="entire-day-checkbox"
                        className="font-poppins font-normal text-sm leading-5 text-[#0F1011] cursor-pointer flex-1"
                      >
                        I'm unavailable the entire day
                      </label>
                      <Checkbox
                        id="entire-day-checkbox"
                        checked={field.value}
                        onChange={(e) => {
                          field.onChange(e.currentTarget.checked)
                        }}
                        size="md"
                        styles={{
                          root: {
                            marginLeft: 'auto'
                          },
                          input: {
                            cursor: 'pointer'
                          }
                        }}
                      />
                    </div>
                  )}
                />
              </div>

              {/* Time Dropdowns - Only show when not full day */}
              {!isFullDay && (
                <div className="px-6 pb-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block mb-2 font-poppins font-medium text-sm text-[#0F1011]">
                        Start Time
                      </label>
                      <Controller
                        name="startTime"
                        control={control}
                        render={({ field }) => (
                          <BaseTimePicker
                            value={field.value || null}
                            onSelect={field.onChange}
                            startTime="00:00"
                            endTime="23:45"
                            interval="00:15"
                          />
                        )}
                      />
                    </div>
                    <div>
                      <label className="block mb-2 font-poppins font-medium text-sm text-[#0F1011]">
                        End Time
                      </label>
                      <Controller
                        name="endTime"
                        control={control}
                        render={({ field }) => (
                          <BaseTimePicker
                            value={field.value || null}
                            onSelect={field.onChange}
                            startTime="00:00"
                            endTime="23:45"
                            interval="00:15"
                          />
                        )}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Optional Reason */}
              <div className="px-6 pb-4">
                <Controller
                  name="reason"
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      {...field}
                      value={field.value || ''}
                      label="Reason"
                      placeholder="Optional reason for blocking calendar"
                      autosize
                      minRows={3}
                      maxRows={5}
                      maxLength={500}
                      error={errors.reason?.message}
                      styles={{
                        label: {
                          fontFamily: 'Poppins, sans-serif',
                          fontWeight: 500,
                          fontSize: '14px',
                          color: '#0F1011',
                          marginBottom: '8px',
                        },
                        input: {
                          fontFamily: 'Poppins, sans-serif',
                          fontSize: '14px',
                          borderRadius: '8px',
                        },
                      }}
                    />
                  )}
                />
              </div>

              {/* Buttons */}
              <Flex
                mt={'lg'}
                className="mx-auto w-full max-w-md px-6"
                gap={'lg'}
                justify={'space-between'}
                align={'center'}
              >
                <Button
                  fullWidth
                  disabled={isSaving}
                  variant="outline"
                  type="button"
                  onClick={() => {
                    reset()
                    setIsOpen(false)
                  }}
                  radius="md"
                  styles={{
                    root: {
                      border: '1px solid #CCCFDB',
                      borderRadius: '8px',
                      padding: '4px 16px',
                      height: 'auto',
                      fontFamily: 'Poppins, sans-serif',
                      fontWeight: 600,
                      fontSize: '14px',
                      lineHeight: '20px',
                      letterSpacing: '0%',
                      textAlign: 'center',
                      color: '#0F1011',
                      '&:hover': {
                        backgroundColor: '#f9fafb',
                      },
                      '&:disabled': {
                        opacity: 0.6,
                        cursor: 'not-allowed',
                      },
                    },
                    label: {
                      padding: '8px 0',
                    },
                  }}
                >
                  Cancel
                </Button>
                <Button
                  fullWidth
                  loading={isSaving}
                  type="submit"
                  radius="md"
                  styles={{
                    root: {
                      border: '1px solid #CCCFDB',
                      borderRadius: '8px',
                      padding: '4px 16px',
                      height: 'auto',
                      fontFamily: 'Poppins, sans-serif',
                      fontWeight: 600,
                      fontSize: '14px',
                      lineHeight: '20px',
                      letterSpacing: '0%',
                      textAlign: 'center',
                      color: '#fff',
                      '&:hover': {
                        backgroundColor: '#1387faff',
                      },
                      '&:disabled': {
                        opacity: 0.6,
                        cursor: 'not-allowed',
                      },
                    },
                    label: {
                      padding: '8px 0',
                    },
                  }}
                >
                  Done
                </Button>
              </Flex>
            </Stack>
          </form>
        </div>
      </div>
    </div>
  )
}

export default BlockCalendarAdd
