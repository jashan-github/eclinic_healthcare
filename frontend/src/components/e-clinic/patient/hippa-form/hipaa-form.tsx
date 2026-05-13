import { useState } from 'react'
import { toast } from 'react-toastify'
import { useSubmitHipaaForm } from '../hook/use-hipaa'
import type { HipaaReleaseFormPayload } from '../service/hipaa-service'

/* ---------------- VALIDATION HELPERS ---------------- */

// Common placeholder strings users sometimes type into signature fields
// when they don't want to fill them out. Matched case-insensitively after
// trimming.
const PLACEHOLDER_SIGNATURES = new Set([
  'test', 'tests', 'testing',
  'asdf', 'asdfasdf',
  'abc', 'abcd', 'abcde',
  '1234', '12345', '123456',
  'xxx', 'xxxx', 'xxxxx',
  'qwer', 'qwerty',
  'foo', 'bar', 'baz',
  'none', 'n/a', 'na',
  '...', 'sign', 'signature'
])

const SIGNATURE_MIN = 2
const SIGNATURE_MAX = 100
const TEXT_MAX = 255
// Section 10 signature must be recent — within the last year. Anything
// older almost certainly indicates a copy-pasted stale date.
const SIGNATURE_DATE_MAX_AGE_DAYS = 365

const isValidDateString = (v: string): boolean => {
  if (!v) return false
  const d = new Date(v)
  return !Number.isNaN(d.getTime())
}

const isPlaceholderSignature = (v: string): boolean =>
  PLACEHOLDER_SIGNATURES.has(v.trim().toLowerCase())

const todayAtMidnight = (): Date => {
  const t = new Date()
  t.setHours(0, 0, 0, 0)
  return t
}

/* ---------------- TYPE DEFINITION ---------------- */

interface HipaaFormData {
  // Section 1
  section1_last_name: string
  section1_first_name: string
  section1_middle_name: string
  section1_date_of_birth: string
  section1_reference_number: string
  section1_address: string
  section1_country: string

  // Section 2
  section2_name: string
  section2_address: string
  section2_country: string

  // Section 3
  section3_name: string
  section3_relationship_to_patient: string
  section3_phone_number: string
  section3_address: string
  section3_country: string

  // Section 4
  section4_expiration_date: string | null
  section4_expiration_event: string | null

  // Section 5 - General Health Info
  section5_medical_records: boolean
  section5_dental_records: boolean
  section5_other_non_specific: boolean
  section5_non_specific_records_details: string

  // Section 6 - Specific Health Info
  section6_communicable_disease: boolean
  section6_communicable_disease_signature: string
  section6_communicable_disease_date: string

  section6_reproductive_health: boolean
  section6_reproductive_health_signature: string
  section6_reproductive_health_date: string

  section6_hiv_test_results: boolean
  section6_hiv_test_results_signature: string
  section6_hiv_test_results_date: string

  section6_mental_health_records: boolean
  section6_mental_health_records_signature: string
  section6_mental_health_records_date: string

  section6_substance_use_disorder: boolean
  section6_substance_use_disorder_signature: string
  section6_substance_use_disorder_date: string

  section6_other: boolean
  section6_other_signature: string
  section6_other_date: string
  section6_other_records_details: string

  section6_psychotherapy_notes: boolean
  section6_psychotherapy_notes_signature: string
  section6_psychotherapy_notes_date: string

  // Section 7 - Purpose
  section7_healthcare: boolean
  section7_research: boolean
  section7_marketing: boolean
  section7_sale: boolean
  section7_legal: boolean
  section7_other: boolean
  section7_other_details: string

  // Section 9
  section9_additional_information: string | null

  // Section 10
  section10_name_of_patient_client: string
  section10_signature_date: string
  section10_name_of_signatory_if_not_patient: string
  section10_authority_to_sign: string
  section10_name_of_translator: string
  section10_signature_of_translator: string
}

interface HipaaFormProps {
  onClose: () => void;
  onSuccess?: () => void;
}

/* ---------------- COMPONENT ---------------- */

const HipaaForm = ({ onClose, onSuccess }: HipaaFormProps) => {
  const { mutate: submitForm, isPending } = useSubmitHipaaForm()

  const [form, setForm] = useState<HipaaFormData>({
    section1_last_name: '',
    section1_first_name: '',
    section1_middle_name: '',
    section1_date_of_birth: '',
    section1_reference_number: '',
    section1_address: '',
    section1_country: '',

    section2_name: '',
    section2_address: '',
    section2_country: '',

    section3_name: '',
    section3_relationship_to_patient: '',
    section3_phone_number: '',
    section3_address: '',
    section3_country: '',

    section4_expiration_date: null,
    section4_expiration_event: null,

    section5_medical_records: false,
    section5_dental_records: false,
    section5_other_non_specific: false,
    section5_non_specific_records_details: '',

    section6_communicable_disease: false,
    section6_communicable_disease_signature: '',
    section6_communicable_disease_date: '',

    section6_reproductive_health: false,
    section6_reproductive_health_signature: '',
    section6_reproductive_health_date: '',

    section6_hiv_test_results: false,
    section6_hiv_test_results_signature: '',
    section6_hiv_test_results_date: '',

    section6_mental_health_records: false,
    section6_mental_health_records_signature: '',
    section6_mental_health_records_date: '',

    section6_substance_use_disorder: false,
    section6_substance_use_disorder_signature: '',
    section6_substance_use_disorder_date: '',

    section6_other: false,
    section6_other_signature: '',
    section6_other_date: '',
    section6_other_records_details: '',

    section6_psychotherapy_notes: false,
    section6_psychotherapy_notes_signature: '',
    section6_psychotherapy_notes_date: '',

    section7_healthcare: false,
    section7_research: false,
    section7_marketing: false,
    section7_sale: false,
    section7_legal: false,
    section7_other: false,
    section7_other_details: '',

    section9_additional_information: null,

    section10_name_of_patient_client: '',
    section10_signature_date: '',
    section10_name_of_signatory_if_not_patient: '',
    section10_authority_to_sign: '',
    section10_name_of_translator: '',
    section10_signature_of_translator: '',
  })

  const [errors, setErrors] = useState<string[]>([])

  const handleChange = (field: keyof HipaaFormData, value: any) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const validateForm = () => {
    const issues: string[] = []
    const today = todayAtMidnight()
    const oldestAllowedSignatureDate = new Date(today)
    oldestAllowedSignatureDate.setDate(oldestAllowedSignatureDate.getDate() - SIGNATURE_DATE_MAX_AGE_DAYS)

    // ----- Required text helper -----
    const requireText = (value: string, label: string, max: number = TEXT_MAX) => {
      const trimmed = value?.trim() ?? ''
      if (!trimmed) issues.push(`${label} is required`)
      else if (trimmed.length > max) issues.push(`${label} must be ${max} characters or fewer`)
    }

    // ----- Section 6 signature + date helper (only fires when checkbox is on) -----
    const requireSignatureBlock = (
      checked: boolean,
      signature: string,
      date: string,
      sectionLabel: string,
      extraDetails?: { value: string; label: string }
    ) => {
      if (!checked) return
      const trimmedSig = signature?.trim() ?? ''
      if (!trimmedSig) {
        issues.push(`${sectionLabel}: signature is required`)
      } else if (trimmedSig.length < SIGNATURE_MIN || trimmedSig.length > SIGNATURE_MAX) {
        issues.push(`${sectionLabel}: signature must be ${SIGNATURE_MIN}-${SIGNATURE_MAX} characters`)
      } else if (isPlaceholderSignature(trimmedSig)) {
        issues.push(`${sectionLabel}: signature looks like a placeholder; please sign with your real name`)
      }
      if (!date) {
        issues.push(`${sectionLabel}: date is required`)
      } else if (!isValidDateString(date)) {
        issues.push(`${sectionLabel}: date is not a valid date`)
      } else if (new Date(date).getTime() > today.getTime()) {
        issues.push(`${sectionLabel}: date cannot be in the future`)
      }
      if (extraDetails && !extraDetails.value.trim()) {
        issues.push(`${sectionLabel}: ${extraDetails.label} is required`)
      }
    }

    // ----- Section 1 -----
    requireText(form.section1_first_name, 'Section 1: First Name')
    requireText(form.section1_last_name, 'Section 1: Last Name')
    if (form.section1_middle_name && form.section1_middle_name.length > TEXT_MAX) {
      issues.push(`Section 1: Middle Name must be ${TEXT_MAX} characters or fewer`)
    }
    if (!form.section1_date_of_birth) {
      issues.push('Section 1: Date of Birth is required')
    } else if (!isValidDateString(form.section1_date_of_birth)) {
      issues.push('Section 1: Date of Birth is not a valid date')
    } else if (new Date(form.section1_date_of_birth).getTime() > today.getTime()) {
      issues.push('Section 1: Date of Birth cannot be in the future')
    }
    requireText(form.section1_address, 'Section 1: Address')
    requireText(form.section1_country, 'Section 1: City/Country/Region')

    // ----- Section 2 -----
    requireText(form.section2_name, 'Section 2: Name')
    requireText(form.section2_address, 'Section 2: Address/Telephone')
    requireText(form.section2_country, 'Section 2: City/Country/Region')

    // ----- Section 3 -----
    requireText(form.section3_name, 'Section 3: Name')
    requireText(form.section3_relationship_to_patient, 'Section 3: Relationship to Patient')
    requireText(form.section3_phone_number, 'Section 3: Telephone Number')
    requireText(form.section3_address, 'Section 3: Address')
    requireText(form.section3_country, 'Section 3: City/Country/Region')

    // ----- Section 4: expiration date OR event -----
    const hasExpirationDate = !!form.section4_expiration_date
    const hasExpirationEvent = !!form.section4_expiration_event?.trim()
    if (!hasExpirationDate && !hasExpirationEvent) {
      issues.push('Section 4: Expiration Date or Event is required (enter N/A in the event field if not applicable)')
    }
    if (hasExpirationDate) {
      const dateStr = form.section4_expiration_date as string
      if (!isValidDateString(dateStr)) {
        issues.push('Section 4: Expiration Date is not a valid date')
      } else if (new Date(dateStr).getTime() <= today.getTime()) {
        issues.push('Section 4: Expiration Date must be in the future')
      }
    }

    // ----- Section 5: at least one selection -----
    if (
      !form.section5_medical_records &&
      !form.section5_dental_records &&
      !form.section5_other_non_specific
    ) {
      issues.push('Section 5: Select at least one type of health information')
    }
    if (form.section5_other_non_specific) {
      requireText(form.section5_non_specific_records_details, 'Section 5: Other (details)', 1000)
    }

    // ----- Section 6: per-row signature + date when checkbox is ticked -----
    requireSignatureBlock(
      form.section6_communicable_disease,
      form.section6_communicable_disease_signature,
      form.section6_communicable_disease_date,
      'Section 6: Communicable Disease'
    )
    requireSignatureBlock(
      form.section6_reproductive_health,
      form.section6_reproductive_health_signature,
      form.section6_reproductive_health_date,
      'Section 6: Reproductive Health'
    )
    requireSignatureBlock(
      form.section6_hiv_test_results,
      form.section6_hiv_test_results_signature,
      form.section6_hiv_test_results_date,
      'Section 6: HIV Test Results'
    )
    requireSignatureBlock(
      form.section6_mental_health_records,
      form.section6_mental_health_records_signature,
      form.section6_mental_health_records_date,
      'Section 6: Mental Health Records'
    )
    requireSignatureBlock(
      form.section6_substance_use_disorder,
      form.section6_substance_use_disorder_signature,
      form.section6_substance_use_disorder_date,
      'Section 6: Substance Use Disorder'
    )
    requireSignatureBlock(
      form.section6_other,
      form.section6_other_signature,
      form.section6_other_date,
      'Section 6: Other',
      { value: form.section6_other_records_details, label: 'records details' }
    )
    requireSignatureBlock(
      form.section6_psychotherapy_notes,
      form.section6_psychotherapy_notes_signature,
      form.section6_psychotherapy_notes_date,
      'Section 6: Psychotherapy Notes'
    )

    // ----- Section 7: at least one purpose -----
    if (
      !form.section7_healthcare &&
      !form.section7_research &&
      !form.section7_marketing &&
      !form.section7_sale &&
      !form.section7_legal &&
      !form.section7_other
    ) {
      issues.push('Section 7: Select at least one purpose for release')
    }
    if (form.section7_other) {
      requireText(form.section7_other_details, 'Section 7: Other purpose details', 1000)
    }

    // ----- Section 9: optional, just max-length -----
    if (
      form.section9_additional_information &&
      form.section9_additional_information.length > 2000
    ) {
      issues.push('Section 9: Additional Information must be 2000 characters or fewer')
    }

    // ----- Section 10: signatory + date constraints -----
    requireText(form.section10_name_of_patient_client, 'Section 10: Name of Patient/Client')
    // The patient name in section 10 is itself the signature line, so reject placeholders.
    if (
      form.section10_name_of_patient_client.trim() &&
      isPlaceholderSignature(form.section10_name_of_patient_client)
    ) {
      issues.push(
        'Section 10: Name of Patient/Client looks like a placeholder; please sign with your real name'
      )
    }
    if (!form.section10_signature_date) {
      issues.push('Section 10: Signature Date is required')
    } else if (!isValidDateString(form.section10_signature_date)) {
      issues.push('Section 10: Signature Date is not a valid date')
    } else {
      const sigDate = new Date(form.section10_signature_date)
      if (sigDate.getTime() > today.getTime()) {
        issues.push('Section 10: Signature Date cannot be in the future')
      } else if (sigDate.getTime() < oldestAllowedSignatureDate.getTime()) {
        issues.push(
          `Section 10: Signature Date is more than ${SIGNATURE_DATE_MAX_AGE_DAYS} days old; please use a current date`
        )
      }
    }
    // Section 10 signatory / translator fields: max-length only (optional copies of authority).
    if (form.section10_name_of_signatory_if_not_patient.length > TEXT_MAX) {
      issues.push(`Section 10: Name of Signatory must be ${TEXT_MAX} characters or fewer`)
    }
    if (form.section10_authority_to_sign.length > TEXT_MAX) {
      issues.push(`Section 10: Authority to Sign must be ${TEXT_MAX} characters or fewer`)
    }
    if (form.section10_name_of_translator.length > TEXT_MAX) {
      issues.push(`Section 10: Name of Translator must be ${TEXT_MAX} characters or fewer`)
    }
    if (form.section10_signature_of_translator.trim()) {
      if (
        form.section10_signature_of_translator.trim().length < SIGNATURE_MIN ||
        form.section10_signature_of_translator.trim().length > SIGNATURE_MAX
      ) {
        issues.push(
          `Section 10: Signature of Translator must be ${SIGNATURE_MIN}-${SIGNATURE_MAX} characters`
        )
      } else if (isPlaceholderSignature(form.section10_signature_of_translator)) {
        issues.push('Section 10: Signature of Translator looks like a placeholder')
      }
    }

    return issues
  }

  const handleSubmit = async () => {
    // Validate form
    const emptyFields = validateForm()

    if (emptyFields.length > 0) {
      setErrors(emptyFields)
      toast.error(`Please fill in all required fields. ${emptyFields.length} field(s) are empty.`)
      // Scroll to top to show error message
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }

    setErrors([])

    // Prepare payload for backend
    const payload: HipaaReleaseFormPayload = {
      ...form,
      section4_expiration_date: form.section4_expiration_date || null,
      section4_expiration_event: form.section4_expiration_event || null,
      section9_additional_information: form.section9_additional_information || null,
    }

    // Submit using mutation hook
    submitForm(payload, {
      onSuccess: () => {
        toast.success('HIPAA form submitted successfully!');
        onSuccess?.();
        onClose();
      },
      onError: (error) => {
        toast.error(error.message || 'Failed to submit HIPAA form');
      }
    });
  }

  const Checkbox = ({
    label,
    field
  }: {
    label: string
    field: keyof HipaaFormData
  }) => (
    <label className="flex items-center gap-2 text-sm font-poppins">
      <input
        type="checkbox"
        checked={form[field] as boolean}
        onChange={(e) => handleChange(field, e.target.checked)}
      />
      <span className="select-none">{label}</span>
    </label>
  )

  return (
    <div className="bg-white w-full max-w-4xl rounded-lg p-8 border-2 border-black font-sans overflow-y-auto max-h-[90vh]">
      {/* HEADER */}
      <div className="text-center mb-6 pb-4 border-b-2 border-black relative">
        <p className="text-xs font-bold mb-1">Salutogena Authorization Form</p>
        <h1 className="text-sm font-bold uppercase">
          Authorization for the Release of Protected Health Information
        </h1>
        <button
          onClick={onClose}
          className="absolute -top-2 right-0 text-3xl hover:text-gray-700 font-bold leading-none"
        >
          ×
        </button>
      </div>

      {/* WARNING */}
      <p className="text-xs text-center mb-4">
        <strong>Please complete all sections of this Salutogena Authorization Form. If any sections are left blank, this form will be invalid. Use N/A if not applicable.</strong>
      </p>

      {/* ERROR MESSAGES */}
      {errors.length > 0 && (
        <div className="bg-red-50 border-2 border-red-500 rounded p-4 mb-6">
          <h4 className="font-bold text-red-800 mb-2 text-sm">
            ⚠️ Please complete the following required fields:
          </h4>
          <ul className="list-disc list-inside text-xs text-red-700 space-y-1">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* PAGE 1 */}
      <div className="mb-6">
        {/* SECTION 1 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 1 – Patient/Client Member Information
          </h3>
          <div className="p-3 space-y-3">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs mb-1">Last Name:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                  value={form.section1_last_name}
                  onChange={(e) => handleChange('section1_last_name', e.target.value)}
                />
              </div>
              <div>
                <p className="text-xs mb-1">First Name:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                  value={form.section1_first_name}
                  onChange={(e) => handleChange('section1_first_name', e.target.value)}
                />
              </div>
              <div>
                <p className="text-xs mb-1">Middle Name:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                  value={form.section1_middle_name}
                  onChange={(e) => handleChange('section1_middle_name', e.target.value)}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs mb-1">Reference No:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                  value={form.section1_reference_number}
                  onChange={(e) => handleChange('section1_reference_number', e.target.value)}
                />
              </div>
              <div>
                <p className="text-xs mb-1">Date of Birth:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                  value={form.section1_date_of_birth}
                  onChange={(e) => handleChange('section1_date_of_birth', e.target.value)}
                />
              </div>
            </div>
            <div>
              <p className="text-xs mb-1">Address:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section1_address}
                onChange={(e) => handleChange('section1_address', e.target.value)}
              />
            </div>
            <div>
              <p className="text-xs mb-1">City/Country/Region:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section1_country}
                onChange={(e) => handleChange('section1_country', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* SECTION 2 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 2 - Individual/Organization Authorized by Signatory to Disclose PHI
          </h3>
          <div className="p-3 space-y-3">
            <div>
              <p className="text-xs mb-1">Name:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section2_name}
                onChange={(e) => handleChange('section2_name', e.target.value)}
              />
            </div>
            <div>
              <p className="text-xs mb-1">Address/Telephone No:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section2_address}
                onChange={(e) => handleChange('section2_address', e.target.value)}
              />
            </div>
            <div>
              <p className="text-xs mb-1">City/Country/Region:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section2_country}
                onChange={(e) => handleChange('section2_country', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* SECTION 3 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 3 - Individual/Organization Authorized by Signatory to Receive PHI
          </h3>
          <div className="p-3 space-y-3">
            <div>
              <p className="text-xs mb-1">Name:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section3_name}
                onChange={(e) => handleChange('section3_name', e.target.value)}
              />
            </div>
            <div>
              <p className="text-xs mb-1">Relationship to Patient/Client Member:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section3_relationship_to_patient}
                onChange={(e) => handleChange('section3_relationship_to_patient', e.target.value)}
              />
            </div>
            <div>
              <p className="text-xs mb-1">Telephone No:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section3_phone_number}
                onChange={(e) => handleChange('section3_phone_number', e.target.value)}
              />
            </div>
            <div>
              <p className="text-xs mb-1">Address:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section3_address}
                onChange={(e) => handleChange('section3_address', e.target.value)}
              />
            </div>
            <div>
              <p className="text-xs mb-1">City/Country/Region:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section3_country}
                onChange={(e) => handleChange('section3_country', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* SECTION 4 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 4 - Authorization Expiration Event or Date
          </h3>
          <div className="p-3">
            <p className="text-xs mb-3">
              Unless otherwise revoked by the patient/plan member, this authorization for the release of PHI to the above-named individual/organization will expire on the event or date specified below. Enter N/A in both fields if the release is ongoing.
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs mb-1">Expiration Event:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                  value={form.section4_expiration_event || ''}
                  onChange={(e) => handleChange('section4_expiration_event', e.target.value)}
                />
              </div>
              <div>
                <p className="text-xs mb-1">Expiration Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                  value={form.section4_expiration_date || ''}
                  onChange={(e) => handleChange('section4_expiration_date', e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* PAGE 2 */}
      <div className="mb-6 border-t-2 border-dashed border-gray-400 pt-6">
        {/* SECTION 5 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 5 – Health Information to be Disclosed - General
          </h3>
          <div className="p-3">
            <p className="text-xs mb-3">
              I authorize the following Protected Health Information to be disclosed:
            </p>
            <div className="flex gap-6 mb-3">
              <Checkbox label="Medical Records" field="section5_medical_records" />
              <Checkbox label="Dental Records" field="section5_dental_records" />
              <label className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={form.section5_other_non_specific}
                  onChange={(e) => handleChange('section5_other_non_specific', e.target.checked)}
                />
                <span className="select-none">Other Non-Specific</span>
              </label>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs whitespace-nowrap">If Other Non-Specific, provide details:</span>
              <input
                className="flex-1 border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section5_non_specific_records_details}
                onChange={(e) => handleChange('section5_non_specific_records_details', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* SECTION 6 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 6 – Health Information to be Disclosed – Specific
          </h3>
          <div className="p-3">
            <p className="text-xs mb-3">
              I authorize the following Protected Health Information to be disclosed:
            </p>

            {/* Communicable Disease */}
            <div className="grid grid-cols-12 gap-2 items-center mb-2">
              <label className="col-span-4 flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={form.section6_communicable_disease}
                  onChange={(e) => handleChange('section6_communicable_disease', e.target.checked)}
                />
                <span className="select-none">Communicable Disease</span>
              </label>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Signature:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_communicable_disease_signature}
                  onChange={(e) => handleChange('section6_communicable_disease_signature', e.target.value)}
                />
              </div>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_communicable_disease_date}
                  onChange={(e) => handleChange('section6_communicable_disease_date', e.target.value)}
                />
              </div>
            </div>

            {/* Reproductive Health */}
            <div className="grid grid-cols-12 gap-2 items-center mb-2">
              <label className="col-span-4 flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={form.section6_reproductive_health}
                  onChange={(e) => handleChange('section6_reproductive_health', e.target.checked)}
                />
                <span className="select-none">Reproductive Health</span>
              </label>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Signature:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_reproductive_health_signature}
                  onChange={(e) => handleChange('section6_reproductive_health_signature', e.target.value)}
                />
              </div>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_reproductive_health_date}
                  onChange={(e) => handleChange('section6_reproductive_health_date', e.target.value)}
                />
              </div>
            </div>

            {/* HIV Test Results */}
            <div className="grid grid-cols-12 gap-2 items-center mb-2">
              <label className="col-span-4 flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={form.section6_hiv_test_results}
                  onChange={(e) => handleChange('section6_hiv_test_results', e.target.checked)}
                />
                <span className="select-none">HIV Test Results</span>
              </label>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Signature:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_hiv_test_results_signature}
                  onChange={(e) => handleChange('section6_hiv_test_results_signature', e.target.value)}
                />
              </div>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_hiv_test_results_date}
                  onChange={(e) => handleChange('section6_hiv_test_results_date', e.target.value)}
                />
              </div>
            </div>

            {/* Mental Health Records */}
            <div className="grid grid-cols-12 gap-2 items-center mb-2">
              <label className="col-span-4 flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={form.section6_mental_health_records}
                  onChange={(e) => handleChange('section6_mental_health_records', e.target.checked)}
                />
                <span className="select-none">Mental Health Records *</span>
              </label>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Signature:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_mental_health_records_signature}
                  onChange={(e) => handleChange('section6_mental_health_records_signature', e.target.value)}
                />
              </div>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_mental_health_records_date}
                  onChange={(e) => handleChange('section6_mental_health_records_date', e.target.value)}
                />
              </div>
            </div>

            {/* Substance Use Disorder */}
            <div className="grid grid-cols-12 gap-2 items-center mb-2">
              <label className="col-span-4 flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={form.section6_substance_use_disorder}
                  onChange={(e) => handleChange('section6_substance_use_disorder', e.target.checked)}
                />
                <span className="select-none">Substance Use Disorder</span>
              </label>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Signature:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_substance_use_disorder_signature}
                  onChange={(e) => handleChange('section6_substance_use_disorder_signature', e.target.value)}
                />
              </div>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_substance_use_disorder_date}
                  onChange={(e) => handleChange('section6_substance_use_disorder_date', e.target.value)}
                />
              </div>
            </div>

            {/* Other */}
            <div className="grid grid-cols-12 gap-2 items-center mb-2">
              <label className="col-span-4 flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={form.section6_other}
                  onChange={(e) => handleChange('section6_other', e.target.checked)}
                />
                <span className="select-none">Other</span>
              </label>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Signature:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_other_signature}
                  onChange={(e) => handleChange('section6_other_signature', e.target.value)}
                />
              </div>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_other_date}
                  onChange={(e) => handleChange('section6_other_date', e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs whitespace-nowrap">If "Other", provide details:</span>
              <input
                className="flex-1 border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section6_other_records_details}
                onChange={(e) => handleChange('section6_other_records_details', e.target.value)}
              />
            </div>

            <p className="text-xs font-bold mb-2">
              * Requests for psychotherapy notes require a separate Salutogena Authorization Form and may not be combined with any other request.
            </p>

            {/* Psychotherapy Notes */}
            <div className="grid grid-cols-12 gap-2 items-center">
              <label className="col-span-4 flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={form.section6_psychotherapy_notes}
                  onChange={(e) => handleChange('section6_psychotherapy_notes', e.target.checked)}
                />
                <span className="select-none">Psychotherapy Notes</span>
              </label>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Signature:</p>
                <input
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_psychotherapy_notes_signature}
                  onChange={(e) => handleChange('section6_psychotherapy_notes_signature', e.target.value)}
                />
              </div>
              <div className="col-span-4">
                <p className="text-xs mb-0.5">Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-0.5 text-xs outline-none bg-transparent"
                  value={form.section6_psychotherapy_notes_date}
                  onChange={(e) => handleChange('section6_psychotherapy_notes_date', e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 7 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 7 - Purpose of the Release or Use of Health Information
          </h3>
          <div className="p-3">
            <div className="flex gap-6 mb-3 flex-wrap">
              <Checkbox label="Healthcare" field="section7_healthcare" />
              <Checkbox label="Research" field="section7_research" />
              <Checkbox label="Marketing" field="section7_marketing" />
              <Checkbox label="Sale" field="section7_sale" />
              <Checkbox label="Legal" field="section7_legal" />
              <label className="flex items-center gap-2 text-sm font-poppins">
                <input
                  type="checkbox"
                  checked={form.section7_other}
                  onChange={(e) => handleChange('section7_other', e.target.checked)}
                />
                <span className="select-none">Other</span>
              </label>
            </div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs whitespace-nowrap">Other (please specify):</span>
              <input
                className="flex-1 border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section7_other_details}
                onChange={(e) => handleChange('section7_other_details', e.target.value)}
              />
            </div>
            <p className="text-xs">
              Note: The sale of PHI authorized by this <strong>Salutogena</strong> Authorization Form will result in remuneration to the party specified in Section 2.
            </p>
          </div>
        </div>
      </div>

      {/* PAGE 3 */}
      <div className="mb-6 border-t-2 border-dashed border-gray-400 pt-6">
        {/* SECTION 8 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 8 - Authorization Information
          </h3>
          <div className="p-3">
            <p className="text-xs font-bold mb-2">I understand the following:</p>
            <div className="text-xs space-y-2">
              <p>1. I authorize the use or disclosure of Protected Health Information as described above for the purpose indicated until such event or time as specified in Section 4.</p>
              <p>2. I have the right to revoke this authorization. To do so I understand I must submit my revocation in writing to the party specified in Section 2. The revocation will prevent further disclosure of my health information by the party specified in Section 2 from the date of receipt. I understand a delay may exist if the party specified in Section 2 is not the covered entity authorized to disclose Protected Health Information to the party specified in Section 2. I also understand that a written revocation is not effective with respect to actions the covered entity or party specified in Section 2 took in reliance on a valid Authorization, or where the Authorization was obtained as a condition of obtaining insurance coverage.</p>
              <p>3. I am signing this authorization voluntarily and understand my entitlement to treatment, payment, enrollment, or eligibility for health plan benefits will not be affected if I do not sign this Salutogena Authorization Form.</p>
              <p>4. If the party specified in Section 3 is not an authorized person/party, the disclosed health information may have become compromised, and may no longer be protected under Salutogena patient privacy policy regulations.</p>
              <p>5. I have a right to receive a copy of this Salutogena Authorization Form.</p>
              <p>6 (if applicable). My substance abuse disorder records are protected under the federal regulations governing the Confidentiality of Substance Use Disorder Patient Records and cannot be redisclosed without my written authorization.</p>
            </div>
          </div>
        </div>

        {/* SECTION 9 */}
        <div className="border-2 border-black mb-4">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 9 - Additional Conditions that Apply to this Salutogena Authorization Form
          </h3>
          <div className="p-3">
            <textarea
              className="w-full border-2 border-black h-24 p-2 text-xs outline-none resize-none"
              value={form.section9_additional_information || ''}
              onChange={(e) => handleChange('section9_additional_information', e.target.value)}
              placeholder="Enter any additional conditions or leave blank"
            />
          </div>
        </div>
      </div>

      {/* PAGE 4 */}
      <div className="border-t-2 border-dashed border-gray-400 pt-6">
        {/* SECTION 10 */}
        <div className="border-2 border-black mb-6">
          <h3 className="font-bold text-xs py-2 px-3 bg-gray-200 border-b-2 border-black">
            Section 10 - Signature by or on Behalf of Patient/Plan Member
          </h3>
          <div className="p-3 space-y-3">
            <div>
              <p className="text-xs mb-1">Name of Patient/Client (Print):</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section10_name_of_patient_client}
                onChange={(e) => handleChange('section10_name_of_patient_client', e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs mb-1">Date:</p>
                <input
                  type="date"
                  className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                  value={form.section10_signature_date}
                  onChange={(e) => handleChange('section10_signature_date', e.target.value)}
                />
              </div>
            </div>

            <div>
              <p className="text-xs mb-1">Name of signatory if not patient/client:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section10_name_of_signatory_if_not_patient}
                onChange={(e) => handleChange('section10_name_of_signatory_if_not_patient', e.target.value)}
              />
            </div>

            <div>
              <p className="text-xs mb-1">Authority to sign on behalf of patient/client:</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section10_authority_to_sign}
                onChange={(e) => handleChange('section10_authority_to_sign', e.target.value)}
              />
            </div>

            <div>
              <p className="text-xs mb-1">Name of translator (if applicable):</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section10_name_of_translator}
                onChange={(e) => handleChange('section10_name_of_translator', e.target.value)}
              />
            </div>

            <div>
              <p className="text-xs mb-1">Signature of translator (if applicable):</p>
              <input
                className="w-full border-b-2 border-black px-1 py-1 text-xs outline-none bg-transparent"
                value={form.section10_signature_of_translator}
                onChange={(e) => handleChange('section10_signature_of_translator', e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* SUBMIT BUTTONS */}
      <div className="flex justify-end gap-3 pt-4 border-t-2 border-black">
        <button
          onClick={onClose}
          className="px-6 py-2 text-sm border-2 border-black rounded hover:bg-gray-100 font-semibold"
          disabled={isPending}
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={isPending}
          className="px-6 py-2 text-sm bg-black text-white rounded hover:bg-gray-800 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPending ? 'Submitting...' : 'Submit HIPAA Form'}
        </button>
      </div>
    </div>
  )
}

export default HipaaForm