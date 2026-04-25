import { ArrowLeftIcon } from "@phosphor-icons/react";
import { useState, useEffect } from "react";
import { toast } from "react-toastify";
import type { Doctor, DoctorService } from "@/services/doctors-service";
import {
  useAppointmentDoctorDetails,
  useConsultationTypes,
} from "@/hooks/use-appointment-doctor-details";
import LoaderCircleAnimated from "@/components/orvo/common/loader-circle-animated";
import AppointmentDetailsStep from "./appointment-details-step";
import AppointmentRequestSubmittedStep from "./appointment-request-submitted-step";
import PaymentStep from "./payment-step";
import ConfirmationStep from "./confirmation-step";
import { useAppointmentRequest } from "../hooks/use-doctor-appointment";

interface BookAppointmentFormProps {
  doctor?: Doctor; // Optional for backward compatibility
  doctorId?: string; // Use this to fetch from API
  serviceId?: DoctorService;
  onBack: () => void;
  onImageError?: (doctorId: string) => void;
  getImageSrc?: (doctor: Doctor) => string;
  formatExperience?: (exp: number | string) => string;
  formatRating?: (rating: number | string) => string;
  formatFee?: (fee: number | string, currency?: string) => string;
  calculateTotal?: (
    consultationFee: number | string,
    intakeFee: number,
  ) => number | string;
}

type Step = 1 | 2 | 3 | 4;

const BookAppointmentForm = ({
  doctor: doctorProp,
  doctorId,
  serviceId,
  onBack,
  // getImageSrc,
  formatExperience,
  // formatRating,
  formatFee,
  calculateTotal,
}: BookAppointmentFormProps) => {
  // All hooks must be called at the top, before any conditional returns
  const [currentStep, setCurrentStep] = useState<Step>(1);
  // const [_imageErrors, setImageErrors] = useState<Set<string>>(new Set())

  // Step 1: Appointment Details
  // Default consultation type will be set based on API response in useEffect
  // null means no type selected yet (when both types are available)
  const [consultationType, setConsultationType] = useState<
    "teleconsultation" | "in-clinic" | null
  >(null);
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split("T")[0],
  );

  const [selectedTime, setSelectedTime] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [showInclinic, setShowInclinic] = useState(false);
  const [showTele, setShowTele] = useState(false);
  const appointmentRequestMutation = useAppointmentRequest();

  // Step 2: Payment Details
  const [referralCode, setReferralCode] = useState("");
  const [cardNumber, setCardNumber] = useState("1234 5678 9012 3456");
  const [cardholderName, setCardholderName] = useState("John Doe");
  const [expiryDate, setExpiryDate] = useState("12/25");
  const [cvv, setCvv] = useState("123");
  const [appointmentStatus, setAppointmentStatus] = useState<string>("PENDING");

  const service_id = serviceId?.id ?? "";

  // Fetch doctor details from API if doctorId is provided
  const {
    data: doctorData,
    isLoading,
    error,
  } = useAppointmentDoctorDetails(
    doctorId || null,
    service_id!,
    selectedDate ?? new Date().toISOString().slice(0, 10),
  );
  const { data: consultationTypeBackend } = useConsultationTypes(
    doctorId || null,
    service_id,
  );

  // Set default consultation type based on API response

  useEffect(() => {
    if (consultationTypeBackend?.consultation_types) {
      const types = consultationTypeBackend.consultation_types;

      // Find available types
      const hasInClinic = types.some(
        (t) => t.mode === "IN_CLINIC" && t.is_available,
      );
      const hasTele = types.some(
        (t) => t.mode === "TELECONSULTATION" && t.is_available,
      );

      // Show radio buttons for each available type
      setShowInclinic(hasInClinic);
      setShowTele(hasTele);

      // If both available: no auto-select, user must pick
      // If only one available: auto-select it
      if (hasInClinic && hasTele) {
        setConsultationType(null);
      } else if (hasInClinic) {
        setConsultationType("in-clinic");
      } else if (hasTele) {
        setConsultationType("teleconsultation");
      } else {
        setConsultationType(null);
      }
    }
  }, [consultationTypeBackend]);

  // Auto-advance from step 2 (appointment request submitted) to step 3 (payment) after 2 seconds
  // useEffect(() => {
  //   if (currentStep === 2) {
  //     const timer = setTimeout(() => {
  //       setCurrentStep(3)
  //     }, 2000) // 2 seconds

  //     return () => clearTimeout(timer)
  //   }
  // }, [currentStep])

  // Use API data if available, otherwise fall back to prop
  const doctor = doctorData || doctorProp;

  // Default helper functions if not provided
  const defaultFormatExperience = (exp: number | string) => {
    return exp === "N/A" ? "N/A" : `${exp} `;
  };

  // const defaultFormatRating = (rating: number | string) => {
  //   if (rating === 'N/A') return 'N/A'
  //   // If rating is already formatted as string with "/5", return as-is
  //   if (typeof rating === 'string' && rating.includes('/5')) {
  //     return rating
  //   }
  //   // Otherwise, format it as number/5
  //   return `${rating}/5`
  // }

  const defaultFormatFee = (fee: number | string) => {
    return fee === "N/A" ? "N/A" : `XCG ${fee}`;
  };

  const defaultCalculateTotal = (
    consultationFee: number | string,
    intakeFee: number,
  ) => {
    if (consultationFee === "N/A") {
      return "N/A";
    }
    return typeof consultationFee === "number"
      ? consultationFee + intakeFee
      : intakeFee;
  };

  const FALLBACK_IMAGE = "/assets/icons/doctor-icon.svg";

  // const defaultGetImageSrc = (doc: Doctor) => {
  //   return imageErrors.has(doc.id) ? FALLBACK_IMAGE : doc.image
  // }

  // Use provided functions or defaults
  const formatExp = formatExperience || defaultFormatExperience;
  // const formatRat = formatRating || defaultFormatRating
  const formatF = formatFee || defaultFormatFee;
  const calcTotal = calculateTotal || defaultCalculateTotal;

  // Show loading state
  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <LoaderCircleAnimated text="Loading healthcare provider details..." />
      </div>
    );
  }

  // Show error state
  if (error || !doctor) {
    return (
      <div className="p-6">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={onBack}
            className="p-2 hover:bg-[#F4F6F9] transition-colors bg-white p-1 rounded-full"
          >
            <ArrowLeftIcon size={20} weight="bold" className="text-[#0F1011]" />
          </button>
          <h1 className="font-poppins font-medium text-lg leading-6 text-[#0F1011]">
            Book Appointment
          </h1>
        </div>
        <div className="text-center py-12">
          <p className="text-red-500 font-poppins text-lg mb-4">
            {error
              ? "Failed to load healthcare provider details. Please try again."
              : "Healthcare provider not found."}
          </p>
          <button
            onClick={onBack}
            className="bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold 
              text-[14px] leading-[20px] py-2.5 px-6 rounded-md transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Static waiver data (can be dynamic later)
  const waiverData = {
    hasWaiver: true,
    intakeFee: 0,
    waivedType: "Full",
    date: "22-Aug-25",
    reason: "Welcome Discount",
    waivedBy: "Dr Robert",
  };

  const total = calcTotal(doctor.consultationFee, doctor.intakeFee);
  const intakeFee = waiverData.hasWaiver
    ? waiverData.intakeFee
    : doctor.intakeFee;
  const finalTotal =
    typeof total === "number"
      ? total
      : typeof doctor.consultationFee === "number"
        ? doctor.consultationFee + intakeFee
        : intakeFee;

  const handleNextFromDetails = (payload: {
    doctor_id: string;
    service_id: string;
    consultation_mode: "IN_CLINIC" | "TELECONSULTATION";
    preferred_date: string;
    preferred_time: string;
    reason: string;
  }) => {
    appointmentRequestMutation.mutate(payload, {
      onSuccess: (response: any) => {
        console.log("📡 Appointment request response:", response);
        // Store the status from API response (check both possible structures)
        const status = response?.status || response?.data?.status || "PENDING";
        console.log("✅ Setting appointment status:", status);
        setAppointmentStatus(status);
        toast.success("Appointment request sent successfully!");
        handleNext();
      },
      onError: (error: any) => {
        toast.error(
          error?.response?.data?.message ||
            "Failed to submit appointment. Please try again.",
        );
      },
    });
  };
  const handleNext = () => {
    if (currentStep === 1) {
      // Validate step 1
      if (!selectedDate || !selectedTime || !symptoms) {
        toast.error("Please fill in all appointment details");
        return;
      }
      setCurrentStep(2);
    } else if (currentStep === 3) {
      // Validate payment step
      if (!cardNumber || !cardholderName || !expiryDate || !cvv) {
        toast.error("Please fill in all payment details");
        return;
      }
      // Go to final confirmation step
      setCurrentStep(4);
    }
  };

  const handlePrevious = () => {
    if (currentStep === 3) {
      // From payment step, go back to appointment details
      setCurrentStep(1);
    } else if (currentStep === 4) {
      // From final confirmation, go back to payment
      setCurrentStep(3);
    } else if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as Step);
    }
  };
  const getDoctorImage = (doctor: Doctor | any) => {
    if ("profile_image" in doctor && doctor.profile_image) {
      return doctor.profile_image;
    }

    return FALLBACK_IMAGE;
  };
  const waiverPercent = doctor.waiver_percent ?? 0;
  const hasWaiver = waiverPercent > 0;

  const originalConsultationFee =
    doctor.amount_before_waiver ?? doctor.consultationFee;
  const renderDoctorInfo = () => (
    <div className="bg-white rounded-lg border border-[#E4E5ED] p-6 h-full">
      {/* Doctor Profile */}
      <div className="flex flex-col items-center mb-6">
        <img
          src={getDoctorImage(doctor)}
          alt={doctor.name}
          onError={(e) => {
            e.currentTarget.src = FALLBACK_IMAGE;
            e.currentTarget.onerror = null;
          }}
          className="w-[120px] h-[120px] rounded-full object-cover border-4 border-[#F4F6F9] mb-4"
        />
        <h3 className="font-poppins font-bold text-[18px] leading-[24px] text-[#0F1011] mb-2">
          {doctor.name}
        </h3>
        <span className="px-4 py-1 bg-[#F1F5F9] bg-opacity-10 rounded-full font-poppins font-medium text-[14px] leading-[20px] text-[#002FD4] mb-4">
          {doctor.specialty}
        </span>
      </div>

      {/* Doctor Details */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
            Experience
          </span>
          <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
            {formatExp(doctor.experience)}
          </span>
        </div>
        {/* <div className="flex justify-between items-center">
          <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
            Rating
          </span>
          <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
            {formatRat(doctor.rating)}
          </span>
        </div> */}
        <div className="flex justify-between items-center">
          <div>
            <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
              Consultation Fee
            </span>{" "}
            <span className="font-poppins text-[#002FD4] font-normal text-[14px] ">
              ({serviceId?.name})
            </span>
          </div>

          <span className="flex items-center gap-0.5 font-poppins text-[14px] leading-[20px]">
            {!hasWaiver && (
              <span className="font-semibold text-[#0F1011]">
                {formatF(doctor.consultationFee, doctor.currency)}
              </span>
            )}

            {hasWaiver && (
              <>
                <span className="text-[#64748B] line-through">
                  {formatF(originalConsultationFee, doctor.currency)}
                </span>

                <span className="text-[#64748B]">→</span>

                <span className="font-semibold text-[#0F1011]">
                  {formatF(doctor.consultationFee, doctor.currency)}
                </span>

                <span className="text-green-600 font-medium">
                  ({waiverPercent}% waiver)
                </span>
              </>
            )}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
            Intake Fee
          </span>
          <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
            {formatF(doctor.intakeFee, doctor.currency)}
          </span>
        </div>
        {/* {doctor.waiver_percent !== 0 && (
          <>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
                Amount before wave
              </span>
              <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
                {doctor.amount_before_waiver &&
                  formatF(doctor.amount_before_waiver, doctor.currency)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
                Waiver
              </span>
              <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
                {doctor.waiver_percent && `${doctor.waiver_percent}%`}
              </span>
            </div>
          </>
        )} */}
        <div className="border-t border-[#E4E5ED] pt-4 mt-4">
          <div className="flex justify-between items-center">
            <span className="font-poppins font-bold text-[16px] leading-[24px] text-[#0F1011]">
              Total
            </span>
            <span className="font-poppins font-bold text-[16px] leading-[24px] text-[#0F1011]">
              {formatF(doctor.total_fee, doctor.currency)}
            </span>
          </div>
        </div>
      </div>

      {/* Waiver Details */}
      {/* {waiverData.hasWaiver && (
        <div className="mt-6 pt-6 border-t border-[#E4E5ED]">
          <h4 className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011] mb-3">
            Waiver Details:
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
                Intake Fee:
              </span>
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                ${waiverData.intakeFee} (Waived)
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
                Waived Type:
              </span>
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {waiverData.waivedType}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
                Date:
              </span>
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {waiverData.date}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
                Reason:
              </span>
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {waiverData.reason}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-black">
                Waived by:
              </span>
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                {waiverData.waivedBy}
              </span>
            </div>
          </div>
        </div>
      )} */}
    </div>
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={onBack}
          className="p-2 hover:bg-[#F4F6F9] transition-colors bg-white p-1 rounded-full"
        >
          <ArrowLeftIcon size={20} weight="bold" className="text-[#0F1011]" />
        </button>
        <h1 className="font-poppins font-medium text-lg leading-6 text-[#0F1011]">
          Book Appointment
        </h1>
      </div>

      {/* Step Indicator - Hidden on step 2 (appointment request submitted) and step 4 (final confirmation) */}
      {/* {currentStep !== 2 && currentStep !== 4 && (
        <div className="mb-6">
          <div className="flex items-center justify-center gap-4">
            <div className={`flex items-center gap-2 ${currentStep >= 1 ? 'text-[#002FD4]' : 'text-[#64748B]'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-poppins font-semibold text-sm ${
                currentStep >= 1 ? 'bg-[#002FD4] text-white' : 'bg-[#E4E5ED] text-[#64748B]'
              }`}>
                {currentStep > 1 ? '✓' : '1'}
              </div>
              <span className="font-poppins font-medium text-sm">Appointment</span>
            </div>
            <div className={`w-12 h-0.5 ${currentStep >= 3 ? 'bg-[#002FD4]' : 'bg-[#E4E5ED]'}`} />
            <div className={`flex items-center gap-2 ${currentStep >= 3 ? 'text-[#002FD4]' : 'text-[#64748B]'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-poppins font-semibold text-sm ${
                currentStep >= 3 ? 'bg-[#002FD4] text-white' : 'bg-[#E4E5ED] text-[#64748B]'
              }`}>
                {currentStep > 3 ? '✓' : '2'}
              </div>
              <span className="font-poppins font-medium text-sm">Payment</span>
            </div>
          </div>
        </div>
      )} */}

      {/* Two Panel Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Panel - Doctor Info (30% width on lg+) */}
        <div className="lg:col-span-4">{renderDoctorInfo()}</div>

        {/* Right Panel - Step Content (70% width on lg+) */}
        <div className="lg:col-span-8">
          {currentStep === 1 && (
            <AppointmentDetailsStep
              consultationType={consultationType}
              selectedDate={selectedDate}
              selectedTime={selectedTime}
              symptoms={symptoms}
              onConsultationTypeChange={setConsultationType}
              onDateChange={setSelectedDate}
              onTimeChange={setSelectedTime}
              onSymptomsChange={setSymptoms}
              onNext={handleNextFromDetails}
              showInclinic={showInclinic}
              showTele={showTele}
              doctorId={doctorId}
              serviceId={serviceId?.id}
            />
          )}
          {currentStep === 2 && (
            <AppointmentRequestSubmittedStep
              doctorName={doctor.name}
              status={appointmentStatus}
            />
          )}
          {currentStep === 3 && (
            <PaymentStep
              referralCode={referralCode}
              cardNumber={cardNumber}
              cardholderName={cardholderName}
              expiryDate={expiryDate}
              cvv={cvv}
              intakeFee={intakeFee}
              consultationFee={doctor.consultationFee}
              totalAmount={finalTotal}
              formatFee={formatF}
              onReferralCodeChange={setReferralCode}
              onCardNumberChange={setCardNumber}
              onCardholderNameChange={setCardholderName}
              onExpiryDateChange={setExpiryDate}
              onCvvChange={setCvv}
              onPrevious={handlePrevious}
              onNext={handleNext}
            />
          )}
          {currentStep === 4 && (
            <ConfirmationStep
              doctorName={doctor.name}
              consultationType={consultationType}
              selectedDate={selectedDate}
              selectedTime={selectedTime}
              symptoms={symptoms}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default BookAppointmentForm;
