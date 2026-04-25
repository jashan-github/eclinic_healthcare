import { useState, type FC, type ReactElement } from 'react'
import VisitsSidebar from './visits-sidebar'
import VisitsDetailsWrapper from './visits-details-wrapper'
import { useParams } from '@tanstack/react-router'
import { usePatientVisits, useRxTemplates } from '../../hooks/use-patient-visits'
import { useRxPdf } from '../../hooks/use-rx-service'

const VisitsWrapper: FC = (): ReactElement => {
  const { patientId } = useParams({ strict: false })
  const { data: visitsData } = usePatientVisits(patientId)
  const [selectedVisitId, setSelectedVisitId] = useState<string | null>(null)
  const [selectedClinicId, setSelectedClinicId] = useState<string>('')

  const { data: rxTemplatesData } = useRxTemplates()

  const selectedVisit = visitsData?.data.records.find(
    (v) => v.id === selectedVisitId
  )

  // Find the rx template that matches the selected clinic location
  const rxTemplateId = rxTemplatesData?.data.templates.find(
    (t) => t.clinic_location_id === selectedClinicId
  )?.id

  const { pdfBlob, isLoading: isPdfLoading, error: pdfError } = useRxPdf(
    patientId || '',
    selectedVisit?.soap_note?.id,
    selectedVisitId || undefined,
    rxTemplateId || undefined
  )

  // Debug logs
  // useEffect(() => {
  //   if (selectedVisitId && selectedClinicId) {
  //     console.log("Trying to fetch RX PDF with:", {
  //       patientId,
  //       soapNoteId: selectedVisit?.soap_note?.id,
  //       appointmentId: selectedVisitId,
  //       rxTemplateId,
  //     })

  //     if (pdfBlob) {
  //       console.log("PDF Blob received!", pdfBlob)
  //     }
  //     if (pdfError) {
  //       console.error("PDF fetch error:", pdfError)
  //     }
  //   }
  // }, [selectedVisitId, selectedClinicId, pdfBlob, pdfError, rxTemplateId])

  return (
    <div className="h-screen p-4">
      <div className="bg-white h-full flex w-full rounded-lg shadow">
        <VisitsSidebar
          visits={visitsData?.data.records || []}
          onVisitSelect={(visitId, soapNoteId) => {
            setSelectedVisitId(visitId)
            console.log("Selected visit ID:", visitId)
            if (soapNoteId) {
              console.log("Selected SOAP note ID:", soapNoteId)
            } else {
              console.log("No SOAP note available for this visit")
            }
          }}
          selectedClinicId={selectedClinicId}
          onClinicChange={setSelectedClinicId}
        />
        <VisitsDetailsWrapper
          pdfBlob={pdfBlob}
          isPdfLoading={isPdfLoading}
          pdfError={pdfError}
        />
      </div>
    </div>
  )
}

export default VisitsWrapper