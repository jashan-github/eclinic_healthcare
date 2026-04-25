import { type FC, type ReactElement, useMemo, useState } from 'react'
import { useCalendarSchedule } from '../hooks/use-calendar-schedule'
import { useBlockCalendarSlots } from '../hooks/use-block-calendar-slots'
import { Calendar } from '@mantine/dates'
import { SegmentedControl, Box, Text, Stack, Tooltip } from '@mantine/core'
import { VideoCamera, Hospital } from '@phosphor-icons/react'

type ServiceDetail = {
  name: string
  mode: string
  time: string
  duration?: number
  amount?: number | string
}

type TimeRange = {
  start: string
  end: string
  services: ServiceDetail[]
}

type DaySchedule = {
  dayFull: string
  dayShort: string
  ranges: TimeRange[]
  services: ServiceDetail[]
}

const HOURS_START = 6
const HOURS_END = 21

function toMinutes(time: string): number {
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
}

const CalendarWeekView: FC = (): ReactElement => {
  const { weeklySchedule } = useCalendarSchedule()
  const { blockedSlots = [] } = useBlockCalendarSlots()
  const [activeDayIdx, setActiveDayIdx] = useState(0)
  const [viewMode, setViewMode] = useState<'week' | 'month'>('week')
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date())

  // Helper function to check if a date is blocked
  const isDateBlocked = useMemo(() => {
    return (date: Date): boolean => {
      if (!date || blockedSlots.length === 0) return false
      
      const checkDate = new Date(date)
      checkDate.setHours(0, 0, 0, 0)
      
      return blockedSlots.some(period => {
        const startDate = new Date(period.start_datetime)
        const endDate = new Date(period.end_datetime)
        startDate.setHours(0, 0, 0, 0)
        endDate.setHours(0, 0, 0, 0)
        
        // Check if the date falls within any blocked period
        return checkDate >= startDate && checkDate <= endDate
      })
    }
  }, [blockedSlots])

  const days: DaySchedule[] = useMemo(() => {
    // Always show all 7 days of the week
    const allDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return allDays.map((dayName) => {
      // Find the schedule data for this day if it exists
      const scheduleDay = (weeklySchedule || []).find(d => d.day_name === dayName)
      
      // Extract services from all schedules for this day
      const services: ServiceDetail[] = []
      const ranges: TimeRange[] = []
      
      if (scheduleDay) {
        scheduleDay.doctor_schedules.forEach((schedule) => {
          const timeRange = schedule.start_time && schedule.end_time 
            ? `${schedule.start_time} - ${schedule.end_time}`
            : ''
          
          // Collect services for this time slot
          const slotServices: ServiceDetail[] = []
          
          if (schedule.appointment_services && schedule.appointment_services.length > 0) {
            schedule.appointment_services.forEach((service) => {
              const serviceDetail: ServiceDetail = {
                name: service.service_name || 'Unnamed Service',
                mode: service.consultation_mode || 'IN_CLINIC',
                time: timeRange,
                duration: typeof service.duration === 'number' ? service.duration : parseInt(String(service.duration || 0)),
                amount: service.amount
              }
              services.push(serviceDetail)
              slotServices.push(serviceDetail)
            })
          }
          
          // Add time range with associated services
          if (schedule.start_time && schedule.end_time) {
            ranges.push({
              start: schedule.start_time,
              end: schedule.end_time,
              services: slotServices
            })
          }
        })
      }
      
      return {
        dayFull: dayName,
        dayShort: dayName.substring(0, 3).toUpperCase(),
        ranges,
        services
      }
    })
  }, [weeklySchedule])

  const hours = useMemo(() => {
    const list: string[] = []
    for (let h = HOURS_START; h <= HOURS_END; h++) {
      const hour12 = ((h + 11) % 12) + 1
      const ampm = h < 12 ? 'AM' : 'PM'
      list.push(`${String(hour12).padStart(2, '0')}:00 ${ampm}`)
    }
    return list
  }, [])

  const totalMinutes = (HOURS_END - HOURS_START) * 60

  // Month view component
  const renderMonthView = () => {
    const formatTime = (time: string) => {
      const [h, m] = time.split(':').map(Number)
      const ampm = h < 12 ? 'AM' : 'PM'
      const hr = ((h + 11) % 12) + 1
      return `${String(hr).padStart(2, '0')}:${String(m).padStart(2, '0')} ${ampm}`
    }

    return (
      <div className="grid grid-cols-[1fr_16px_320px] gap-6">
        {/* Left: Calendar */}
        <Box>
          <Text size="lg" fw={600} mb="md">Month View</Text>
          <Calendar
            getDayProps={(dateStr: string) => {
              const date = new Date(dateStr)
              const isBlocked = isDateBlocked(date)
              const isSelected = selectedDate?.toDateString() === date.toDateString()
              
              return {
                selected: isSelected,
                disabled: isBlocked,
                onClick: () => {
                  if (!isBlocked) {
                    setSelectedDate(date)
                  }
                },
                style: isBlocked ? {
                  opacity: 0.4,
                  cursor: 'not-allowed',
                  textDecoration: 'line-through',
                  backgroundColor: '#f5f5f5'
                } : {}
              }
            }}
            size="xl"
            styles={{
              month: {
                width: '100%'
              }
            }}
          />
        </Box>

        {/* Vertical Divider */}
        <div className="h-full" style={{ borderRight: '2px solid #E4E5ED' }} />

        {/* Right: Selected Date Details */}
        <div className="h-full">
          <div
            style={{
              fontFamily: 'Poppins',
              fontWeight: 700,
              fontSize: '16px',
              lineHeight: '22px',
              color: '#0F1011',
              marginBottom: '16px',
            }}
          >
            {selectedDate ? selectedDate.toLocaleDateString('en-US', { 
              weekday: 'long', 
              month: 'long', 
              day: 'numeric' 
            }) : 'Select a date'}
          </div>

          {(() => {
            if (!selectedDate) {
              return (
                <Box p="md" bg="gray.1" style={{ borderRadius: '8px' }}>
                  <Text size="sm" c="dimmed">
                    Select a date to view services
                  </Text>
                </Box>
              )
            }

            // Get the day name for the selected date
            const dayName = selectedDate.toLocaleDateString('en-US', { weekday: 'long' })
            const dayData = days.find(d => d.dayFull === dayName)
            
            if (!dayData || (dayData.services.length === 0 && dayData.ranges.length === 0)) {
              return (
                <Box p="md" bg="gray.1" style={{ borderRadius: '8px' }}>
                  <Text size="sm" c="dimmed">
                    No services scheduled for this day
                  </Text>
                </Box>
              )
            }

            return (
              <Stack gap="lg">
                {/* Time Slots Section */}
                <div>
                  <Text
                    size="sm"
                    c="dimmed"
                    mb="sm"
                    style={{
                      fontFamily: 'Poppins',
                      fontWeight: 600,
                      fontSize: '12px',
                    }}
                  >
                    Available Time Slots:
                  </Text>
                  {dayData.ranges.length > 0 ? (
                    <Stack gap="sm">
                      {dayData.ranges.map((range, idx) => (
                        <Box
                          key={idx}
                          p="sm"
                          bg="green.0"
                          style={{
                            borderRadius: '8px',
                            border: '1px solid #93D1AC',
                          }}
                        >
                          <Text
                            fw={500}
                            style={{
                              fontFamily: 'Poppins',
                              fontSize: '14px',
                              color: '#0F1011',
                            }}
                          >
                            {formatTime(range.start)} - {formatTime(range.end)}
                          </Text>
                        </Box>
                      ))}
                    </Stack>
                  ) : (
                    <Box p="md" bg="gray.1" style={{ borderRadius: '8px' }}>
                      <Text
                        size="sm"
                        c="dimmed"
                        style={{
                          fontFamily: 'Poppins',
                          fontSize: '13px',
                        }}
                      >
                        No time slots available for this day
                      </Text>
                    </Box>
                  )}
                </div>

                {/* Services Section */}
                <div>
                  <Text
                    size="sm"
                    c="dimmed"
                    mb="sm"
                    style={{
                      fontFamily: 'Poppins',
                      fontWeight: 600,
                      fontSize: '12px',
                    }}
                  >
                    Services Available:
                  </Text>
                  {dayData.services.length > 0 ? (
                    <Stack gap="sm">
                      {dayData.services.map((service, idx) => (
                        <Box
                          key={idx}
                          style={{
                            borderLeft: '4px solid #10B981',
                            paddingLeft: '12px',
                            paddingTop: '8px',
                            paddingBottom: '8px',
                            backgroundColor: '#F9FAFB',
                            borderRadius: '4px'
                          }}
                        >
                          <Text
                            fw={500}
                            style={{
                              fontFamily: 'Poppins',
                              fontSize: '14px',
                              color: '#0F1011',
                              lineHeight: '20px'
                            }}
                          >
                            {service.name}
                          </Text>
                        </Box>
                      ))}
                    </Stack>
                  ) : (
                    <Box p="md" bg="gray.1" style={{ borderRadius: '8px' }}>
                      <Text
                        size="sm"
                        c="dimmed"
                        style={{
                          fontFamily: 'Poppins',
                          fontSize: '13px',
                        }}
                      >
                        No services available for this day
                      </Text>
                    </Box>
                  )}
                </div>
              </Stack>
            )
          })()}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full" style={{ background: 'transparent' }}>
      {/* Outer container */}
      <div
        style={{
          background: '#fff',
          borderRadius: '12px',
          padding: '20px',
          boxShadow: '6px 7px 20px 0px #0000001A',
          maxWidth: '90%',
          width: '100%',
          margin: '0 auto'
        }}
      >
        {/* View Mode Toggle */}
        <Box mb="xl">
          <div className="flex items-center justify-between mb-4">
            <div
              style={{
                fontFamily: 'Poppins',
                fontWeight: 600,
                fontSize: '16px',
                lineHeight: '22px',
                color: '#0F1011',
                verticalAlign: 'middle',
              }}
            >
              Calendar View
            </div>
            <SegmentedControl
              value={viewMode}
              onChange={(value) => setViewMode(value as 'week' | 'month')}
              data={[
                { label: 'Week View', value: 'week' },
                { label: 'Month View', value: 'month' }
              ]}
              styles={{
                root: {
                  backgroundColor: '#F4F6F9'
                },
                label: {
                  fontFamily: 'Poppins',
                  fontSize: '14px',
                  fontWeight: 600
                }
              }}
            />
          </div>
        </Box>

        {/* Conditional Rendering Based on View Mode */}
        {viewMode === 'month' ? (
          renderMonthView()
        ) : (
          <div className="grid grid-cols-[1fr_16px_320px] gap-6">
            <div className="overflow-x-auto">
              <div className="min-w-[800px]">
                {/* Week View Content */}
                <div
                  style={{
                    fontFamily: 'Poppins',
                    fontWeight: 600,
                    fontSize: '14px',
                    lineHeight: '20px',
                    color: '#0F1011',
                    verticalAlign: 'middle',
                    marginBottom: '12px',
                  }}
                >
                  Week Schedule
                </div>

                {/* Header row: time corner + day names across X */}
                <div className="grid grid-cols-[80px_repeat(7,minmax(0,1fr))] mb-1">
                  <div />
                  {days.map((d, idx) => (
                    <button
                      key={`${d.dayFull}-head`}
                      type="button"
                      className={`rounded transition-colors px-2 py-1 ${
                        idx === activeDayIdx
                          ? 'bg-[#F4F6F9] text-[#0F1011]'
                          : 'text-[#0F1011]/70 hover:bg-gray-50'
                      }`}
                      style={{
                        fontFamily: 'Poppins',
                        fontWeight: 700,
                        fontSize: '12px',
                        lineHeight: '18px',
                        textAlign: 'center',
                        verticalAlign: 'middle',
                      }}
                      onClick={() => setActiveDayIdx(idx)}
                    >
                      {d.dayShort}
                    </button>
                  ))}
                </div>

                {/* Body grid */}
                <div className="grid grid-cols-[80px_repeat(7,minmax(0,1fr))] min-h-[560px]">
                  {/* Time labels */}
                  <div className="relative pb-2">
                    {hours.map((h, idx) => {
                      const isLast = idx === hours.length - 1
                      return (
                        <div
                          key={h}
                          className={`absolute ${isLast ? '' : '-translate-y-1/2'}`}
                          style={{
                            fontFamily: 'Poppins',
                            fontWeight: 300,
                            fontSize: '12px',
                            lineHeight: '12px',
                            color: '#9C9EB9',
                            verticalAlign: 'middle',
                            ...(isLast
                              ? { bottom: 0 }
                              : { top: `${(idx / (hours.length - 1)) * 100}%` }),
                          }}
                        >
                          {h}
                        </div>
                      )
                    })}
                  </div>

                  {/* Day columns - All 7 days */}
                  {days.map((d, idx) => (
                    <div
                      key={`${d.dayFull}-col`}
                      className="relative cursor-pointer hover:bg-gray-50/50"
                      onClick={() => setActiveDayIdx(idx)}
                    >
                      {/* Horizontal hour lines */}
                      {hours.map((_, hourIdx) => {
                        const isLast = hourIdx === hours.length - 1
                        return (
                          <div
                            key={hourIdx}
                            className={`absolute left-0 right-0 ${isLast ? 'border-b' : 'border-t'}`}
                            style={
                              isLast
                                ? { bottom: 0, borderColor: '#E4E5ED' }
                                : { top: `${(hourIdx / (hours.length - 1)) * 100}%`, borderColor: '#E4E5ED' }
                            }
                          />
                        )
                      })}

                      {/* Availability blocks vertically with service details */}
                      {d.ranges.map((r, i) => {
                        const start = Math.max(0, toMinutes(r.start) - HOURS_START * 60)
                        const end = Math.min(totalMinutes, toMinutes(r.end) - HOURS_START * 60)
                        const top = (start / totalMinutes) * 100
                        const ideal = ((end - start) / totalMinutes) * 100
                        const height = Math.min(100 - top, Math.max(2, ideal))
                        
                        const formatTime = (time: string) => {
                          const [h, m] = time.split(':').map(Number)
                          const ampm = h < 12 ? 'AM' : 'PM'
                          const hr = ((h + 11) % 12) + 1
                          return `${String(hr).padStart(2, '0')}:${String(m).padStart(2, '0')} ${ampm}`
                        }

                        // Build tooltip content
                        const tooltipContent = (
                          <div>
                            <Text size="xs" fw={600} mb={4}>
                              {formatTime(r.start)} - {formatTime(r.end)}
                            </Text>
                            {r.services.length > 0 ? (
                              <Stack gap={4}>
                                {r.services.map((service, sIdx) => (
                                  <div key={sIdx}>
                                    <Text size="xs" fw={500}>
                                      {service.name}
                                    </Text>
                                    <Text size="xs" c="dimmed">
                                      {service.mode === 'TELECONSULTATION' ? '💻 Video' : '🏥 In-Clinic'}
                                      {service.duration ? ` • ${service.duration} mins` : ''}
                                      {service.amount ? ` • $${service.amount}` : ''}
                                    </Text>
                                  </div>
                                ))}
                              </Stack>
                            ) : (
                              <Text size="xs" c="dimmed">Available for booking</Text>
                            )}
                          </div>
                        )

                        return (
                          <Tooltip
                            key={i}
                            label={tooltipContent}
                            position="top"
                            withArrow
                            multiline
                            w={220}
                          >
                            <div
                              className="absolute left-2 right-2 rounded overflow-hidden"
                              style={{
                                top: `${top}%`,
                                height: `${height}%`,
                                background: '#E7F2EA',
                                border: '1px solid #93D1AC',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease'
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.background = '#D1E7DD'
                                e.currentTarget.style.borderColor = '#75B798'
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.background = '#E7F2EA'
                                e.currentTarget.style.borderColor = '#93D1AC'
                              }}
                            >
                              {/* Service content inside block */}
                              <div className="px-1 py-0.5 h-full flex flex-col justify-center">
                                {r.services.length > 0 ? (
                                  r.services.length === 1 ? (
                                    // Single service - show full name
                                    <div className="text-[10px] leading-tight">
                                      <div className="flex items-center gap-0.5 mb-0.5">
                                        {r.services[0].mode === 'TELECONSULTATION' ? (
                                          <VideoCamera size={10} weight="fill" className="text-[#10B981] flex-shrink-0" />
                                        ) : (
                                          <Hospital size={10} weight="fill" className="text-[#10B981] flex-shrink-0" />
                                        )}
                                        <span className="font-semibold text-[#0F1011] truncate">
                                          {r.services[0].name.length > 15 
                                            ? `${r.services[0].name.substring(0, 15)}...` 
                                            : r.services[0].name}
                                        </span>
                                      </div>
                                      {height > 15 && (
                                        <div className="text-[9px] text-gray-600">
                                          {formatTime(r.start).replace(' ', '')}
                                        </div>
                                      )}
                                    </div>
                                  ) : (
                                    // Multiple services - show count
                                    <div className="text-[10px] leading-tight text-center">
                                      <div className="font-semibold text-[#0F1011]">
                                        {r.services.length} Services
                                      </div>
                                      {height > 15 && (
                                        <div className="text-[9px] text-gray-600">
                                          {formatTime(r.start).replace(' ', '')}
                                        </div>
                                      )}
                                    </div>
                                  )
                                ) : (
                                  // No services - show time only
                                  <div className="text-[10px] text-center text-gray-600">
                                    {formatTime(r.start).replace(' ', '')}
                                  </div>
                                )}
                              </div>
                            </div>
                          </Tooltip>
                        )
                      })}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Vertical Divider */}
            <div className="h-full" style={{ borderRight: '2px solid #E4E5ED' }} />

            {/* Right Panel - Selected Day Details */}
            <div className="h-full">
              <div
                style={{
                  fontFamily: 'Poppins',
                  fontWeight: 700,
                  fontSize: '16px',
                  lineHeight: '22px',
                  color: '#0F1011',
                  marginBottom: '16px',
                }}
              >
                {days[activeDayIdx]?.dayFull || ''}
              </div>

              {(() => {
                const selectedDay = days[activeDayIdx]
                const ranges = selectedDay?.ranges || []
                const services = selectedDay?.services || []

                const formatTime = (time: string) => {
                  const [h, m] = time.split(':').map(Number)
                  const ampm = h < 12 ? 'AM' : 'PM'
                  const hr = ((h + 11) % 12) + 1
                  return `${String(hr).padStart(2, '0')}:${String(m).padStart(2, '0')} ${ampm}`
                }

                return (
                  <Stack gap="lg">
                    {/* Time Slots Section */}
                    <div>
                      <Text
                        size="sm"
                        c="dimmed"
                        mb="sm"
                        style={{
                          fontFamily: 'Poppins',
                          fontWeight: 600,
                          fontSize: '12px',
                        }}
                      >
                        Available Time Slots:
                      </Text>
                      {ranges.length > 0 ? (
                        <Stack gap="sm">
                          {ranges.map((range, idx) => (
                            <Box
                              key={idx}
                              p="sm"
                              bg="green.0"
                              style={{
                                borderRadius: '8px',
                                border: '1px solid #93D1AC',
                              }}
                            >
                              <Text
                                fw={500}
                                style={{
                                  fontFamily: 'Poppins',
                                  fontSize: '14px',
                                  color: '#0F1011',
                                }}
                              >
                                {formatTime(range.start)} - {formatTime(range.end)}
                              </Text>
                            </Box>
                          ))}
                        </Stack>
                      ) : (
                        <Box p="md" bg="gray.1" style={{ borderRadius: '8px' }}>
                          <Text
                            size="sm"
                            c="dimmed"
                            style={{
                              fontFamily: 'Poppins',
                              fontSize: '13px',
                            }}
                          >
                            No time slots available for this day
                          </Text>
                        </Box>
                      )}
                    </div>

                    {/* Services Section */}
                    <div>
                      <Text
                        size="sm"
                        c="dimmed"
                        mb="sm"
                        style={{
                          fontFamily: 'Poppins',
                          fontWeight: 600,
                          fontSize: '12px',
                        }}
                      >
                        Services Available:
                      </Text>
                      {services.length > 0 ? (
                        <Stack gap="sm">
                          {services.map((service, idx) => (
                            <Box
                              key={idx}
                              style={{
                                borderLeft: '4px solid #10B981',
                                paddingLeft: '12px',
                                paddingTop: '8px',
                                paddingBottom: '8px',
                                backgroundColor: '#F9FAFB',
                                borderRadius: '4px'
                              }}
                            >
                              <Text
                                fw={500}
                                style={{
                                  fontFamily: 'Poppins',
                                  fontSize: '14px',
                                  color: '#0F1011',
                                  lineHeight: '20px'
                                }}
                              >
                                {service.name}
                              </Text>
                            </Box>
                          ))}
                        </Stack>
                      ) : (
                        <Box p="md" bg="gray.1" style={{ borderRadius: '8px' }}>
                          <Text
                            size="sm"
                            c="dimmed"
                            style={{
                              fontFamily: 'Poppins',
                              fontSize: '13px',
                            }}
                          >
                            No services available for this day
                          </Text>
                        </Box>
                      )}
                    </div>
                  </Stack>
                )
              })()}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CalendarWeekView

/* 
  ============================================
  COMMENTED OUT - EXISTING IMPLEMENTATION
  ============================================
  The original week view implementation has been enhanced with:
  - Month/Week view toggle
  - All 7 days displayed in week view
  - Right panel showing selected day details with time slots
  
  Original features preserved:
  - 7-day week view with time slots (6 AM - 9 PM)
  - Click on day to see schedule details
  - Green blocks showing availability ranges
  - Right panel showing selected day details
  ============================================
*/
