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
                value={cardNumber}
                onChange={(e) => onCardNumberChange(e.target.value)}
                placeholder="1234 5678 9012 3456"
                className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                  font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                  placeholder:text-[#A5ABB3D9] placeholder:font-medium
                  focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
              />
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
                className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                  font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                  placeholder:text-[#A5ABB3D9] placeholder:font-medium
                  focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
                  Expiry Date
                </label>
                <input
                  type="text"
                  value={expiryDate}
                  onChange={(e) => onExpiryDateChange(e.target.value)}
                  placeholder="MM/YY"
                  className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                    placeholder:text-[#A5ABB3D9] placeholder:font-medium
                    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
                />
              </div>
              <div>
                <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
                  CVV
                </label>
                <input
                  type="text"
                  value={cvv}
                  onChange={(e) => onCvvChange(e.target.value)}
                  placeholder="123"
                  className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
                    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
                    placeholder:text-[#A5ABB3D9] placeholder:font-medium
                    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
                />
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
            onClick={onNext}
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

