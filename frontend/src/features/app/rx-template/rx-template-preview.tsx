import { useEffect, useState, type FC } from 'react'

type LetterheadData =
  | null
  | 'loading' // ✅ Add loading state
  | string // for custom uploaded image OR backend URL
  | { type: 'default'; doctorName: string; qualification: string; clinicAddress: string }

const RxTemplatePreview: FC = () => {
  const [letterhead, setLetterhead] = useState<LetterheadData>('loading')

  useEffect(() => {
    const update = () => {
      setLetterhead((window.__LETTERHEAD__ as LetterheadData) || null)
    }
    update()
    window.addEventListener('letterheadChanged', update)
    return () => window.removeEventListener('letterheadChanged', update)
  }, [])

  useEffect(() => {
    const style = document.createElement('style')
    style.textContent = `
      @media print {
        @page { size: A4; margin: 0; }
        body * { visibility: hidden; }
        #a4-preview, #a4-preview * { visibility: visible; }
        #a4-preview {
          position: absolute;
          left: 0; top: 0;
          width: 210mm;
          min-height: 297mm;
          padding: 20mm 30mm;
          background: white;
        }
        .custom-letterhead-bg {
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
          background-color: white !important;
        }
      }
    `
    document.head.appendChild(style)
    return () => {
      if (document.head.contains(style)) document.head.removeChild(style)
    }
  }, [])

  // Check if letterhead is loading
  const isLoading = letterhead === 'loading'
  
  // Check if letterhead is a custom image (uploaded or from backend URL)
  const isCustomImage = typeof letterhead === 'string' && letterhead.trim() !== '' && letterhead !== 'loading'
  
  // Check if letterhead is default type
  const isDefault = letterhead && typeof letterhead === 'object' && 'type' in letterhead && letterhead.type === 'default'
  
  console.log("letterhead", letterhead)
  console.log("isLoading", isLoading)
  console.log("isCustomImage", isCustomImage)
  console.log("isDefault", isDefault)

  return (
    <div className="bg-gray-100 flex items-center justify-center p-8">
      {/* Loading State - Full Screen */}
      {isLoading ? (
        <div className="flex items-center justify-center" style={{ width: '210mm', minHeight: '297mm' }}>
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
            <p className="text-gray-700 text-xl font-semibold">Loading...</p>
          </div>
        </div>
      ) : (
      <div
        id="a4-preview"
        className="bg-white shadow-2xl relative overflow-hidden"
        style={{
          width: '210mm',
          minHeight: '297mm',
          maxWidth: '100%',
          aspectRatio: '210 / 297',
        }}
      >

        {/* Custom Uploaded Letterhead OR Backend Letterhead URL */}
        {isCustomImage && (
          <div
            className="custom-letterhead-bg absolute top-0 left-0 right-0 h-56 bg-contain bg-no-repeat bg-top pointer-events-none"
            style={{ backgroundImage: `url(${letterhead})` }}
          />
        )}

        {/* Default Letterhead Template */}
        {isDefault && (
          <div className="flex items-center justify-between pt-10 pb-8 border-b-2 border-gray-300">
            {/* Logo */}
            <div className="flex-shrink-0">
              <img
                src="/assets/icons/e-clinic-logo-full.svg"
                alt="Clinic Logo"
                className="h-16 object-contain"
              />
            </div>

            {/* Doctor Name & Qualification */}
            <div className="text-center flex-1 px-8">
              <h1
                style={{
                  fontFamily: 'Poppins, sans-serif',
                  fontWeight: 700,
                  fontSize: '20.4px',
                  lineHeight: '30px',
                  letterSpacing: '0%',
                  color: '#002FD4',
                  margin: 0,
                }}
              >
                Dr. {letterhead.doctorName}
              </h1>
              <p
                style={{
                  fontFamily: 'Poppins, sans-serif',
                  fontWeight: 400,
                  fontSize: '16.35px',
                  lineHeight: '24px',
                  letterSpacing: '0%',
                  color: '#0F1011',
                  margin: '4px 0 0',
                }}
              >
                {letterhead.qualification}
              </p>
            </div>

            {/* Clinic Address */}
            <div className="text-right flex-shrink-0">
              <p
                style={{
                  fontFamily: 'Poppins, sans-serif',
                  fontWeight: 700,
                  fontSize: '20.4px',
                  lineHeight: '30px',
                  letterSpacing: '0%',
                  color: '#002FD4',
                  margin: 0,
                }}
              >
                Clinic Address
              </p>
              <p
                style={{
                  fontFamily: 'Poppins, sans-serif',
                  fontWeight: 400,
                  fontSize: '16.35px',
                  lineHeight: '24px',
                  letterSpacing: '0%',
                  color: '#0F1011',
                  margin: '6px 0 0',
                  whiteSpace: 'pre-line',
                }}
              >
                {letterhead.clinicAddress}
              </p>
            </div>
          </div>
        )}

        {/* Content Area */}
        <div className={isDefault ? "mt-40 px-12" : "mt-64 px-12"}>
          {/* Prescription content will go here */}
        </div>
      </div>
      )}
    </div>
  )
}

export default RxTemplatePreview