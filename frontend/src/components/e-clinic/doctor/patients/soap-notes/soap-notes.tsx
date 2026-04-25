// components/SoapNotes.tsx
import { type FC, useState, useMemo } from 'react'
import { PencilIcon, PlusIcon } from '@phosphor-icons/react'
import { format, parseISO } from 'date-fns'
import { usePatientSoapNotes, useCreateSoapNote, useUpdateSoapNote } from '@/hooks/use-doctor-soap-notes'
import SoapNotesFormModal from './soap-notes-form-modal'
import GlobalLoader from '@/components/orvo/common/global-loader'
import type { SoapNote } from '@/services/doctor-soap-notes-service'
import { toast } from 'react-toastify'

interface SoapNotesProps {
  patientId: string
  appointmentId?: string
}

interface SoapSection {
  letter: string
  title: string
  content: string
}

const SoapNotes: FC<SoapNotesProps> = ({ patientId, appointmentId }) => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSoapNote, setEditingSoapNote] = useState<SoapNote | null>(null)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')

  const { data: soapNotesData, isLoading, error } = usePatientSoapNotes(patientId)
  const { mutate: createSoapNote, isPending: isCreating } = useCreateSoapNote()
  const { mutate: updateSoapNote, isPending: isUpdating } = useUpdateSoapNote()

  const soapNotes = soapNotesData?.data?.soap_notes || []

  // Debug: Log appointmentId received
  console.log('SOAP Notes Component - Appointment ID:', appointmentId)
  console.log('SOAP Notes Component - Patient ID:', patientId)

  // Group SOAP notes by month
  const groupedNotes = useMemo(() => {
    const groups: Record<string, SoapNote[]> = {}
    
    soapNotes.forEach((note) => {
      const date = parseISO(note.created_at)
      const monthYear = format(date, 'MMMM yyyy')
      
      if (!groups[monthYear]) {
        groups[monthYear] = []
      }
      groups[monthYear].push(note)
    })

    // Sort notes within each group by date (most recent first)
    Object.keys(groups).forEach((key) => {
      groups[key].sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    })

    return groups
  }, [soapNotes])

  const handleAddNew = () => {
    setEditingSoapNote(null)
    setModalMode('create')
    setIsModalOpen(true)
  }

  const handleEdit = (note: SoapNote) => {
    setEditingSoapNote(note)
    setModalMode('edit')
    setIsModalOpen(true)
  }

  const handleFormSubmit = (data: { subjective: string; objective: string; assessment: string; plan: string }) => {
    if (modalMode === 'create') {
      if (!appointmentId) {
        toast.error('No appointment available for this patient today. Please create an appointment first.')
        return
      }
      createSoapNote(
        {
          patientId,
          payload: {
            appointment_id: appointmentId,
            patient_id: patientId,
            ...data
          }
        },
        {
          onSuccess: () => {
            setIsModalOpen(false)
          },
          onError: (error: any) => {
            // Check if SOAP note already exists
            if (error?.response?.data?.message?.includes('already exists')) {
              // Close modal and show message suggesting to edit
              setIsModalOpen(false)
              toast.warning('A SOAP note already exists for this appointment. Please edit the existing note instead.', {
                autoClose: 5000
              })
            }
            // Error toast is already shown by the hook
          }
        }
      )
    } else if (editingSoapNote) {
      updateSoapNote(
        {
          patientId,
          soapNoteId: editingSoapNote.id,
          payload: data
        },
        {
          onSuccess: () => {
            setIsModalOpen(false)
            setEditingSoapNote(null)
          }
        }
      )
    }
  }

  const parseSoapContent = (content: string): string[] => {
    return content.split(',').map(item => item.trim()).filter(item => item.length > 0)
  }

  if (isLoading) {
    return <GlobalLoader />
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl max-w-[1138px] p-6">
        <div className="text-center text-red-500">Failed to load SOAP notes</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl max-w-[1138px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="font-poppins font-semibold text-lg leading-7 tracking-[-0.45px] text-[#002FD4]">
          SOAP Notes
        </div>
        {soapNotes.length === 0 && (
          <div className="flex items-center gap-3">
            <button
              onClick={handleAddNew}
              className="flex items-center justify-center gap-3 w-[171px] h-11 rounded-md bg-[#002FD4] px-0 py-3.5 hover:bg-[#001FB8] transition-colors"
            >
              <PlusIcon weight="bold" color="white" />
              <span className="font-poppins font-semibold text-sm leading-5 text-white">
                Add New
              </span>
            </button>
          </div>
        )}
      </div>

      {/* SOAP Notes List */}
      {soapNotes.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No SOAP notes available for this patient
        </div>
      ) : (
        <div className="space-y-6 mt-10">
          {Object.entries(groupedNotes).map(([monthYear, notes]) => (
            <div key={monthYear} className="space-y-4">
              <p className="font-poppins font-semibold text-lg leading-7 text-[#0F1011]">
                {monthYear}
              </p>
              {notes.map((note) => {
                const sections: SoapSection[] = [
                  {
                    letter: 'S',
                    title: 'Subjective',
                    content: note.subjective
                  },
                  {
                    letter: 'O',
                    title: 'Objective',
                    content: note.objective
                  },
                  {
                    letter: 'A',
                    title: 'Assessment',
                    content: note.assessment
                  },
                  {
                    letter: 'P',
                    title: 'Plan',
                    content: note.plan
                  }
                ]

                return (
                  <div key={note.id} className="border border-[#E5E7EB] p-4 space-y-4 rounded-lg">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span className="font-poppins font-normal text-sm leading-5 text-[#6B7280]">
                        {format(parseISO(note.created_at), "d MMMM, yyyy 'at' hh:mm a")}
                      </span>
                      <button 
                        className="flex items-center gap-1"
                        onClick={() => handleEdit(note)}
                      >
                        <PencilIcon size={14} color="#002FD4" weight="bold" />
                        <span className="font-poppins font-semibold text-sm leading-5 text-center text-[#002FD4]">
                          Edit
                        </span>
                      </button>
                    </div>

                    {/* SOAP Sections */}
                    {sections.map((section) => {
                      const items = parseSoapContent(section.content)
                      return (
                        <div key={section.letter} className="flex gap-4">
                          <div className="w-10 h-10 rounded-md flex items-center justify-center text-2xl leading-8 font-bold shrink-0 bg-[#E8EEFD] text-[#002FD4]">
                            {section.letter}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="font-poppins font-semibold text-base leading-6 text-[#0F1011]">
                              {section.title}
                            </div>
                            <ul className="text-sm text-gray-600 space-y-0.5">
                              {items.map((item, idx) => (
                                <li
                                  key={idx}
                                  className="pl-4 relative before:absolute before:left-0 before:content-['-'] before:text-[#0F1011] font-poppins font-normal text-sm leading-5 text-[#0F1011]"
                                >
                                  {item}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      )}

      {/* Form Modal */}
      <SoapNotesFormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setEditingSoapNote(null)
        }}
        onSubmit={handleFormSubmit}
        isLoading={isCreating || isUpdating}
        soapNote={editingSoapNote}
        mode={modalMode}
      />
    </div>
  )
}

export default SoapNotes
