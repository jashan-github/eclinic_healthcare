import {
  CalendarIcon,
  ChatCircleIcon,
  VideoCameraIcon,
  ClockIcon,
  MapPinIcon,
  SealCheckIcon,
} from "@phosphor-icons/react";
import { Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
// import RatingModal from './rating-modal'
import { usePatientAppointments } from "../hook/use-patient-appointments";
// import type { PatientAppointment } from '../service/patient-appointment-service'
import { formatDate, formatFee, formatTime } from "@/utils/helper";
import {
  useInitializePayment,
  usePaymentStatus,
} from "../hook/use-appointment-payment";
import { toast } from "react-toastify";
import { useNavigate } from "@tanstack/react-router";
import AgoraVideoCallRoom from "../../doctor/webinars/agora-video-call-room";
import { useJoinVideoSession } from "@/hooks/use-video-call";
import { StethoscopeIcon } from "@phosphor-icons/react";

const PatientAppointments = () => {
  const [activeTab, setActiveTab] = useState<"upcoming" | "pending" | "past">(
    "upcoming",
  );
  const [currentPaymentId, setCurrentPaymentId] = useState<string | null>(null);
  const [isPollingPayment, setIsPollingPayment] = useState(false);
  const [processingAppointmentId, setProcessingAppointmentId] = useState<
    string | null
  >(null);
  const [activeAppointment, setActiveAppointment] = useState<{
    sessionId: string;
  } | null>(null);
  const [active, setActive] = useState(false);
  const [initialJoinData, setInitialJoinData] = useState<any>(null);

  const joinSession = useJoinVideoSession();

  const { data, isLoading, isError, refetch } = usePatientAppointments();
  const { mutate: initializePayment, isPending: isInitializing } =
    useInitializePayment();
  const { data: paymentStatus } = usePaymentStatus(
    currentPaymentId,
    isPollingPayment,
  );
  const navigate = useNavigate();

  const appointments = data ? data[activeTab] : [];
  const FALLBACK_IMAGE = "/assets/icons/doctor-icon.svg";

  const tabs = [
    {
      label: "Upcoming",
      value: "upcoming" as const,
      count: data?.upcoming.length || 0,
    },
    {
      label: "Pending",
      value: "pending" as const,
      count: data?.pending.length || 0,
    },
    { label: "Past", value: "past" as const, count: data?.past.length || 0 },
  ];

  // Handle payment status changes
  useEffect(() => {
    if (paymentStatus?.data && paymentStatus.data !== null) {
      if (
        paymentStatus.data.is_paid &&
        paymentStatus.data.appointment_confirmed
      ) {
        toast.success("Payment successful! Appointment confirmed.");
        setIsPollingPayment(false);
        setCurrentPaymentId(null);
        setProcessingAppointmentId(null);
        // Refetch appointments data without page reload
        setTimeout(() => {
          refetch();
        }, 1000);
      } else if (paymentStatus.data.status === "FAILED") {
        toast.error("Payment failed. Please try again.");
        setIsPollingPayment(false);
        setCurrentPaymentId(null);
        setProcessingAppointmentId(null);
        // Refetch appointments data without page reload
        setTimeout(() => {
          refetch();
        }, 1000);
      } else if (paymentStatus.data.status === "CANCELLED") {
        toast.warning("Payment was cancelled.");
        setIsPollingPayment(false);
        setCurrentPaymentId(null);
        setProcessingAppointmentId(null);
        // Refetch appointments data without page reload
        setTimeout(() => {
          refetch();
        }, 1000);
      } else if (paymentStatus.data.status === "PENDING") {
        // For pending/processing status, refetch after a delay to check for updates
        setIsPollingPayment(false);
        setCurrentPaymentId(null);
        setProcessingAppointmentId(null);
        // Refetch appointments data without page reload
        setTimeout(() => {
          refetch();
        }, 2000);
      }
    }
  }, [paymentStatus, refetch]);

  // Stop polling after 5 minutes to prevent infinite polling
  useEffect(() => {
    if (isPollingPayment) {
      const timeout = setTimeout(
        () => {
          setIsPollingPayment(false);
          setCurrentPaymentId(null);
          toast.info(
            "Payment status check timed out. Please refresh the page to see updated status.",
          );
        },
        5 * 60 * 1000,
      ); // 5 minutes

      return () => clearTimeout(timeout);
    }
  }, [isPollingPayment]);

  // Note: URL parameter checking removed since we're using popup window instead of redirect

  const handlePaymentClick = (appointmentRequestId: string) => {
    initializePayment(appointmentRequestId, {
      onSuccess: (response) => {
        if (response.success && response.data.payment_url) {
          // Open payment URL in popup window
          const popup = window.open(
            response.data.payment_url,
            "Payment",
            "width=800,height=600,scrollbars=yes,resizable=yes,left=" +
              (window.screen.width / 2 - 400) +
              ",top=" +
              (window.screen.height / 2 - 300),
          );

          if (!popup) {
            toast.error("Please allow popups to proceed with payment");
            return;
          }

          // Set payment ID for polling
          setCurrentPaymentId(response.data.payment_id);
          setIsPollingPayment(true);

          // Listen for message from popup payment pages (success, failure, processing)
          const handleMessage = (event: MessageEvent) => {
            // Only accept messages from same origin
            if (event.origin !== window.location.origin) return;

            if (
              event.data &&
              (event.data.type === "PAYMENT_SUCCESS" ||
                event.data.type === "PAYMENT_FAILURE" ||
                event.data.type === "PAYMENT_PROCESSING")
            ) {
              // Stop polling first
              setIsPollingPayment(false);
              setCurrentPaymentId(null);
              setProcessingAppointmentId(null);

              // Close popup if still open
              if (!popup.closed) {
                popup.close();
              }

              // Refetch appointments data without page reload
              setTimeout(() => {
                refetch();
              }, 1000);
            }
          };

          window.addEventListener("message", handleMessage);

          // Check if popup is closed and refetch data
          const checkPopupClosed = setInterval(() => {
            if (popup.closed) {
              clearInterval(checkPopupClosed);

              // Stop polling
              setIsPollingPayment(false);
              setCurrentPaymentId(null);
              setProcessingAppointmentId(null);

              // Remove message listener
              window.removeEventListener("message", handleMessage);

              // Refetch appointments data without page reload
              setTimeout(() => {
                refetch();
              }, 1000);
            }
          }, 1000);
        } else {
          toast.error(response.message || "Failed to initialize payment");
          setProcessingAppointmentId(null);
        }
      },
      onError: (error: any) => {
        toast.error(
          error?.response?.data?.message || "Failed to initialize payment",
        );
        setProcessingAppointmentId(null);
      },
    });
  };

  if (isLoading)
    return <div className="p-10 text-center">Loading appointments...</div>;
  if (isError)
    return (
      <div className="p-10 text-center text-red-500">
        Failed to load appointments
      </div>
    );

  const handleSendMessage = (chat_room_id: string) => {
    if (chat_room_id) {
      navigate({ to: `/app/messages/${chat_room_id}` });
    } else {
      toast.error("Chat not available");
    }
  };

  const handleJoinCall = async (appointment: any) => {
    const session_id = appointment.session_id;

    if (!session_id) {
      toast.error("Session ID missing");
      return;
    }

    try {
      const response = await joinSession.mutateAsync(session_id);

      if (response.data.both_ready && response.data.token) {
        setInitialJoinData(response.data);
        setActiveAppointment({ sessionId: session_id });
        setActive(true);
      } else if (response.data.waiting_room) {
        setInitialJoinData(response.data);
        setActiveAppointment({ sessionId: session_id });
        setActive(true);
      } else {
        toast.info(response.data.message || "Waiting for other party...");
      }
    } catch {
      toast.error("Unable to start call");
    }
  };

  // Update the AgoraWebinarRoom render at the end
  if (active && activeAppointment) {
    return (
      <AgoraVideoCallRoom
        sessionId={activeAppointment.sessionId}
        initialJoinData={initialJoinData}
        onLeave={() => {
          setActive(false);
          setActiveAppointment(null);
          setInitialJoinData(null);
          // Reload page to get fresh session
          window.location.reload();
        }}
      />
    );
  }

  return (
    <div className="p-6 bg-[#F4F6F9] min-h-screen overflow-scroll">
      {/* Header Section */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="font-poppins font-medium text-lg leading-6 text-[#0F1011]">
          Manage your healthcare appointments
        </h2>
        <Link
          to="/app/doctors"
          className="bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold 
            text-[14px] leading-[20px] py-2.5 px-6 rounded-md transition-colors"
        >
          Book Appointment
        </Link>
      </div>

      {/* Tabs - New Style matching EditProfileSection */}
      <div className="bg-white rounded-lg border border-[#E4E5ED] mb-6">
        <div className="w-full p-2">
          <div className="flex w-full bg-[#F1F5F9] rounded-lg border border-[#E4E5ED]">
            {tabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setActiveTab(tab.value)}
                className={`flex-1 py-2.5 rounded-md transition-all flex items-center justify-center gap-2 hover:cursor-pointer ${
                  activeTab === tab.value
                    ? "bg-[#002FD4] text-white shadow-sm"
                    : "bg-[#F1F5F9] text-[#545D69] hover:bg-[#F4F6F9]"
                }`}
              >
                <span className="font-poppins font-semibold text-sm leading-5 text-center align-middle">
                  {tab.label} ({tab.count})
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Appointment Cards */}
        <div className="p-6">
          {appointments.length === 0 ? (
            <div className="text-center py-12">
              <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
                No {activeTab} appointments
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {appointments.map((appointment) => {
                const waiverPercent = appointment.waiver_percent ?? 0;
                const hasWaiver = waiverPercent > 0;

                const originalAmount =
                  appointment.amount_before_waiver ?? appointment.price_amount;
                return (
                  <div
                    key={appointment.id}
                    className="bg-white rounded-lg border border-[#E4E5ED] p-6 hover:shadow-md transition-shadow"
                  >
                    <div className="flex gap-6">
                      {/* Left: Healthcare Provider Info */}
                      <div className="flex-shrink-0">
                        <img
                          src={
                            appointment.doctor_profile_image || FALLBACK_IMAGE
                          }
                          alt={FALLBACK_IMAGE}
                          className="w-16 h-16 rounded-full object-cover"
                          onError={(e) => {
                            e.currentTarget.src = FALLBACK_IMAGE;
                            e.currentTarget.onerror = null;
                          }}
                        />
                      </div>

                      {/* Middle: Appointment Details */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h3 className="font-poppins font-bold text-[18px] leading-[24px] text-[#0F1011] mb-1">
                              {appointment.doctor_name}
                            </h3>
                            <p className="font-poppins font-normal text-[14px] text-[#002FD4] leading-[20px] mb-2">
                              {appointment.specialty ||
                                appointment.doctor_specialty ||
                                "General Practice"}
                            </p>
                            {appointment.service_name && (
                              <div
                                className="inline-flex items-center gap-2 mb-2 px-3 py-1 rounded-full
               bg-[#EEF2FF] text-[#1E40AF] max-w-fit"
                                title={appointment.service_name}
                              >
                                <StethoscopeIcon size={14} weight="bold" />
                                <span className="font-poppins text-[13px] leading-[18px] font-medium truncate max-w-[220px]">
                                  {appointment.service_name}
                                </span>
                              </div>
                            )}
                            <div className="flex items-center gap-2">
                              {appointment.consultation_mode ===
                              "TELECONSULTATION" ? (
                                <>
                                  <VideoCameraIcon
                                    size={16}
                                    weight="bold"
                                    className="text-[#002FD4]"
                                  />
                                  <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                                    Tele Consultation
                                  </span>
                                </>
                              ) : (
                                <>
                                  <MapPinIcon
                                    size={16}
                                    weight="bold"
                                    className="text-[#002FD4]"
                                  />
                                  <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                                    In-clinic Consultation
                                  </span>
                                </>
                              )}
                            </div>
                          </div>

                          {/* Status Badge */}
                          {(appointment.status === "ACCEPTED" ||
                            appointment.status === "CONFIRMED") && (
                            <div className="bg-blue-50 flex flex-row p-1 rounded-xl gap-1 px-2">
                              <SealCheckIcon
                                size={16}
                                weight="bold"
                                className="text-[#002FD4]"
                              />
                              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                                {appointment.status === "CONFIRMED"
                                  ? "Confirmed"
                                  : "Accepted"}
                              </span>
                            </div>
                          )}
                        </div>

                        <div className="space-y-3">
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <CalendarIcon
                                size={16}
                                weight="bold"
                                className="text-[#64748B]"
                              />
                              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                                {formatDate(
                                  appointment.appointment_date ||
                                    appointment.preferred_date ||
                                    "",
                                )}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <ClockIcon
                                size={16}
                                weight="bold"
                                className="text-[#64748B]"
                              />
                              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                                {formatTime(
                                  appointment.start_time ||
                                    appointment.preferred_time,
                                )}
                              </span>
                            </div>
                          </div>

                          {appointment.reason && (
                            <div>
                              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
                                Symptoms:{" "}
                              </span>
                              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                                {appointment.reason}
                              </span>
                            </div>
                          )}

                          <div className="flex items-center gap-2 text-[14px] leading-[20px] font-poppins">
                            {!hasWaiver && (
                              <>
                                <span className="text-[#64748B]">
                                  Total Fee:
                                </span>
                                <span className="font-semibold text-[#002FD4]">
                                  {formatFee(
                                    appointment.price_amount,
                                    appointment.currency,
                                  )}
                                </span>
                              </>
                            )}

                            {hasWaiver && (
                              <>
                                <span className="text-[#64748B] line-through">
                                  {formatFee(
                                    originalAmount,
                                    appointment.currency,
                                  )}
                                </span>

                                <span className="text-[#64748B]">→</span>

                                <span className="font-semibold text-[#002FD4]">
                                  {formatFee(
                                    appointment.price_amount,
                                    appointment.currency,
                                  )}
                                </span>

                                <span className="text-green-600 font-medium">
                                  ({waiverPercent}% waiver)
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Right: Action Buttons */}
                      <div className="flex flex-col items-end gap-3">
                        {appointment.payment_status === "paid" &&
                          appointment.status === "CONFIRMED" &&
                          appointment.consultation_mode ===
                            "TELECONSULTATION" &&
                          activeTab === "upcoming" && (
                            <button
                              className="flex items-center gap-2 px-4 py-2 bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold 
                          text-[14px] leading-[20px] rounded-md transition-colors"
                              onClick={() => handleJoinCall(appointment)}
                              // disabled={creating}
                            >
                              <VideoCameraIcon size={16} weight="bold" />
                              Join Video Call
                            </button>
                          )}
                        {activeTab === "upcoming" && (
                          <button
                            disabled={!appointment.chat_room_id}
                            onClick={() =>
                              appointment.chat_room_id &&
                              handleSendMessage(appointment.chat_room_id)
                            }
                            className={`flex items-center gap-2 px-4 py-2 bg-white border border-[#E4E5ED]
                          text-[#0F1011] font-poppins font-semibold text-[14px] leading-[20px]
                          rounded-md transition-colors
                          ${
                            !appointment.chat_room_id
                              ? "opacity-50 cursor-not-allowed"
                              : "hover:bg-[#F4F6F9]"
                          }`}
                          >
                            <ChatCircleIcon size={16} weight="bold" />
                            Message Healthcare Provider
                          </button>
                        )}
                        {/* {activeTab === 'past' && (
                        <button
                          onClick={() => handleRatingClick(appointment)}
                          className="px-4 py-2 bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold 
                            text-[14px] leading-[20px] rounded-md transition-colors"
                        >
                          Give A Rating
                        </button>
                      )} */}
                        {activeTab === "upcoming" &&
                          (appointment.status === "ACCEPTED" ||
                            appointment.status === "CONFIRMED") &&
                          (appointment.payment_status === "pending" ||
                            appointment.payment_status === "processing" ||
                            appointment.payment_status === "failed") && (
                            <button
                              onClick={() => handlePaymentClick(appointment.id)}
                              disabled={
                                processingAppointmentId === appointment.id &&
                                (isInitializing || isPollingPayment)
                              }
                              className={`px-4 py-2 font-poppins font-semibold text-[14px] leading-[20px] rounded-md transition-colors ${
                                processingAppointmentId === appointment.id &&
                                (isInitializing || isPollingPayment)
                                  ? "bg-gray-400 cursor-not-allowed text-white"
                                  : "bg-[#002FD4] hover:bg-[#001FB8] text-white"
                              }`}
                            >
                              {processingAppointmentId === appointment.id &&
                              isInitializing
                                ? "Initializing..."
                                : processingAppointmentId === appointment.id &&
                                    isPollingPayment
                                  ? "Processing..."
                                  : appointment.payment_status === "failed"
                                    ? "Retry Payment"
                                    : "Payment"}
                            </button>
                          )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Rating Modal */}
      {/* {
        selectedAppointment && (
          <RatingModal
            isOpen={ratingModalOpen}
            onClose={handleCloseRatingModal}
            doctorName={selectedAppointment.doctor_name}
            doctorSpecialty={selectedAppointment.doctor_specialty!}
            doctorImage={selectedAppointment.doctor_profile_image!}
            onSubmit={handleRatingSubmit}
          />
        )
      } */}
    </div>
  );
};

export default PatientAppointments;
