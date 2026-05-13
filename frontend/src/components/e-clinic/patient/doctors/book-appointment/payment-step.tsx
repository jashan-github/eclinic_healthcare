import { useState } from 'react'
import { toast } from 'react-toastify'
import { z } from 'zod'

// Luhn algorithm for card-number checksum.
const luhnCheck = (digits: string): boolean => {
  if (!/^\d+$/.test(digits)) return false
  let sum = 0
  let alt = false
  for (let i = digits.length - 1; i >= 0; i--) {
    let n = parseInt(digits.charAt(i), 10)
    if (alt) {
      n *= 2
      if (n > 9) n -= 9
    }
    sum += n
    alt = !alt
  }
  return sum % 10 === 0
}

const paymentSchema = z.object({
  cardNumber: z
    .string()
    .transform((v) => v.replace(/\s/g, ''))
    .pipe(
      z
        .string()
        .regex(/^\d{13,19}$/, 'Card number must be 13-19 digits')
        .refine(luhnCheck, 'Card number is invalid')
    ),
  cardholderName: z
    .string()
    .trim()
    .min(2, 'Cardholder name must be at least 2 characters')
    .max(100, 'Cardholder name must be 100 characters or fewer')
    .regex(/^[A-Za-z .'-]+$/, 'Cardholder name contains invalid characters'),
  expiryDate: z
    .string()
    .regex(/^(0[1-9]|1[0-2])\/\d{2}$/, 'Expiry must be in MM/YY format')
    .refine((v) => {
      const [mm, yy] = v.split('/')
      const month = parseInt(mm, 10)
      const year = 2000 + parseInt(yy, 10)
      // Cards are valid through the LAST day of the given month.
      const lastDayOfMonth = new Date(year, month, 0, 23, 59, 59)
      return lastDayOfMonth.getTime() >= Date.now()
    }, 'Card has expired'),
  cvv: z.string().regex(/^\d{3,4}$/, 'CVV must be 3 or 4 digits')
})

interface PaymentStepProps {
  referralCode: string
  cardNumber: string
  cardholderName: string
  expiryDate: string
  cvv: string
  intakeFee: number
  consultationFee: number | string
  totalAmount: number
  formatFee: (fee: number | string) => string
  onReferralCodeChange: (code: string) => void
  onCardNumberChange: (number: string) => void
  onCardholderNameChange: (name: string) => void
  onExpiryDateChange: (date: string) => void
  onCvvChange: (cvv: string) => void
  onPrevious: () => void
  onNext: (payload: any) => void
}

const PaymentStep = ({
  referralCode,
  cardNumber,
  cardholderName,
  expiryDate,
  cvv,
  intakeFee,
  consultationFee,
  totalAmount,
  formatFee,
  onReferralCodeChange,
  onCardNumberChange,
  onCardholderNameChange,
  onExpiryDateChange,
  onCvvChange,
  onPrevious,
  onNext
}: PaymentStepProps) => {
  const [fieldErrors, setFieldErrors] = useState<{
    cardNumber?: string
    cardholderName?: string
    expiryDate?: string
    cvv?: string
  }>({})

  const handlePayClick = () => {
    const result = paymentSchema.safeParse({
      cardNumber,
      cardholderName,
      expiryDate,
      cvv
    })
    if (!result.success) {
      const errs: typeof fieldErrors = {}
      for (const issue of result.error.issues) {
        const key = issue.path[0] as keyof typeof errs
        if (key && !errs[key]) errs[key] = issue.message
      }
      setFieldErrors(errs)
      toast.error(result.error.issues[0]?.message || 'Please fix payment errors')
      return
    }
    setFieldErrors({})
    onNext(result.data)
  }

  return (
    <div className="bg-white rounded-lg border border-[#E4E5ED] p-6">
      <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#0F1011] mb-6">
        Payment
      </h2>

      <div className="space-y-6">
        {/* Referral Code */}
        <div>
          <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
            Apply Referral Code (if any)
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={referralCode}
              onChange={(e) => onReferralCodeChange(e.target.value)}
              placeholder="Enter referral code"
              className="flex-1 px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                placeholder:text-[#A5ABB3D9] placeholder:font-medium
                focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
            />
            <button
              type="button"
              className="px-6 py-2.5 bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold 
                text-[14px] leading-[20px] rounded-md transition-colors"
            >
              Apply
            </button>
          </div>
        </div>

        {/* Payment Summary */}
        <div className="border-t border-[#E4E5ED] pt-4">
          <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-4">
            Payment Summary
          </h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#545D69]">
                Intake/Membership Fee:
              </span>
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                ${intakeFee}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#545D69]">
                Consultation Fee:
              </span>
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {formatFee(consultationFee)}
              </span>
            </div>
            <div className="border-t border-[#E4E5ED] pt-2 mt-2">
              <div className="flex justify-between items-center">
                <span className="font-poppins font-bold text-[16px] leading-[24px] text-[#0F1011]">
                  Total Amount:
                </span>
                <span className="font-poppins font-bold text-[16px] leading-[24px] text-[#0F1011]">
                  ${totalAmount}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Payment Method */}
        <div>
          <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-4">
            Payment Method
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
                Card Number
              </label>
              <input
                type="text"
                inputMode="numeric"
                value={cardNumber}
                onChange={(e) => onCardNumberChange(e.target.value)}
                placeholder="1234 5678 9012 3456"
                maxLength={23}
                aria-invalid={!!fieldErrors.cardNumber}
                className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA]
                  font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                  placeholder:text-[#A5ABB3D9] placeholder:font-medium
                  focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
              />
              {fieldErrors.cardNumber && (
                <p className="mt-1 font-poppins text-[12px] text-red-600">{fieldErrors.cardNumber}</p>
              )}
            </div>
            <div>
              <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
                Cardholder Name
              </label>
              <input
                type="text"
                value={cardholderName}
                onChange={(e) => onCardholderNameChange(e.target.value)}
                placeholder="John Doe"
                maxLength={100}
                aria-invalid={!!fieldErrors.cardholderName}
                className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA]
                  font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                  placeholder:text-[#A5ABB3D9] placeholder:font-medium
                  focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
              />
              {fieldErrors.cardholderName && (
                <p className="mt-1 font-poppins text-[12px] text-red-600">{fieldErrors.cardholderName}</p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
                  Expiry Date
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  value={expiryDate}
                  onChange={(e) => onExpiryDateChange(e.target.value)}
                  placeholder="MM/YY"
                  maxLength={5}
                  aria-invalid={!!fieldErrors.expiryDate}
                  className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA]
                    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                    placeholder:text-[#A5ABB3D9] placeholder:font-medium
                    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
                />
                {fieldErrors.expiryDate && (
                  <p className="mt-1 font-poppins text-[12px] text-red-600">{fieldErrors.expiryDate}</p>
                )}
              </div>
              <div>
                <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
                  CVV
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  value={cvv}
                  onChange={(e) => onCvvChange(e.target.value)}
                  placeholder="123"
                  maxLength={4}
                  aria-invalid={!!fieldErrors.cvv}
                  className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA]
                    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                    placeholder:text-[#A5ABB3D9] placeholder:font-medium
                    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
                />
                {fieldErrors.cvv && (
                  <p className="mt-1 font-poppins text-[12px] text-red-600">{fieldErrors.cvv}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between pt-4 border-t border-[#E4E5ED]">
          <button
            type="button"
            onClick={onPrevious}
            className="px-6 py-2.5 bg-white border border-[#E4E5ED] hover:bg-[#F4F6F9] text-[#0F1011] font-poppins font-semibold 
              text-[14px] leading-[20px] rounded-md transition-colors"
          >
            Previous
          </button>
          <button
            type="button"
            onClick={handlePayClick}
            className="px-6 py-2.5 bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold
              text-[14px] leading-[20px] rounded-md transition-colors"
          >
            Pay & Submit
          </button>
        </div>
      </div>
    </div>
  )
}

export default PaymentStep

