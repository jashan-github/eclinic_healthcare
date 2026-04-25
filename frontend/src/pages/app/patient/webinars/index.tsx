import { useState, useEffect } from "react";
import { toast } from "react-toastify";
import WebinarSummaryCards from "@/components/e-clinic/patient/webinars/webinar-summary-cards";
import WebinarCard from "@/components/e-clinic/patient/webinars/webinar-card";
import WebinarRegistrationModal from "@/components/e-clinic/patient/webinars/webinar-registration-modal";
import { useHeaderStore } from "@/store/use-header-store";
import {
  usePatientWebinars,
  type TransformedWebinar,
} from "@/hooks/use-patient-webinars";
import AgoraWebinarRoom from "@/components/e-clinic/doctor/webinars/agora-webinar-room";
import { useAuth } from "@/context/auth/auth-context-utils";
import { useRegisterForWebinar } from "@/hooks/use-webinar-registeration";

const PatientWebinarsPage = () => {
  const { setPageTitle } = useHeaderStore();
  const { user } = useAuth();
  const [selectedWebinar, setSelectedWebinar] =
    useState<TransformedWebinar | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeWebinar, setActiveWebinar] = useState<TransformedWebinar | null>(
    null,
  );
  const { mutate: registerWebinar } = useRegisterForWebinar();

  // Fetch webinars from API
  const {
    webinars,
    totalWebinars,
    freeWebinars,
    registeredWebinars,
    isLoading,
    error,
  } = usePatientWebinars();

  useEffect(() => {
    setPageTitle("Webinars");
  }, [setPageTitle]);

  const handleRegisterClick = (webinar: TransformedWebinar) => {
    setSelectedWebinar(webinar);
    setIsModalOpen(true);
  };

  const handleRegister = (webinarId: string) => {
    if (!webinarId) {
      toast.error("Webinar ID not available");
      return;
    }

    registerWebinar(
      { webinar_id: webinarId },
      {
        onSuccess: (response) => {
          const paymentUrl = response?.data?.payment?.payment_url;

          if (paymentUrl) {
            const popup = window.open(
              paymentUrl,
              "Payment",
              "width=800,height=600,scrollbars=yes,resizable=yes",
            );

            if (!popup) {
              toast.error("Please allow popups to proceed with payment");
            }
            return;
          }

          // Free webinar success
          toast.success("Registered successfully");
          setIsModalOpen(false);
          setSelectedWebinar(null);
        },
        onError: () => {
          // toast already handled in hook, optional extra message
          toast.error("Registration failed");
        },
      },
    );
  };

  const handleJoinWebinar = (webinar: TransformedWebinar) => {
    if (!webinar.can_join) {
      toast.error("Webinar is not ready to join yet.");
      return;
    }

    console.log("Joining webinar:", webinar);
    setActiveWebinar(webinar);
  };

  const handleLeaveWebinar = () => {
    setActiveWebinar(null);
    toast.info("Left the webinar");
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedWebinar(null);
  };

  if (activeWebinar) {
    return (
      <AgoraWebinarRoom
        webinarId={activeWebinar.id}
        isHost={false}
        userRole="patient"
        userName={user?.name || "Patient"}
        onLeave={handleLeaveWebinar}
      />
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-[#F4F6F9]">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="font-poppins font-bold text-[28px] leading-[36px] text-[#0F1011] mb-2">
            Webinars
          </h1>
          <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
            Learn from expert doctors and healthcare professional
          </p>
        </div>

        {/* Summary Cards */}
        <WebinarSummaryCards
          totalWebinars={totalWebinars}
          freeWebinars={freeWebinars}
          registeredWebinars={registeredWebinars}
        />

        {/* Upcoming Webinars */}
        <div className="mb-6">
          <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#0F1011] mb-6">
            Upcoming Webinars
          </h2>

          {isLoading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#002FD4]"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-500 mb-4">Failed to load webinars</p>
              <p className="text-gray-500">{error.message}</p>
            </div>
          ) : webinars.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No upcoming webinars available</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {webinars.map((webinar) => (
                <WebinarCard
                  key={webinar.id}
                  webinar={webinar}
                  onRegister={handleRegisterClick}
                  onJoin={handleJoinWebinar}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Registration Modal */}
      <WebinarRegistrationModal
        webinar={selectedWebinar}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onRegister={handleRegister}
        is_registered={selectedWebinar?.is_registered ?? false}
        can_join={selectedWebinar?.can_join ?? false}
        hostId={selectedWebinar?.host_id}
        onJoinWebinar={() => {
          if (selectedWebinar) handleJoinWebinar(selectedWebinar);
          setIsModalOpen(false);
        }}
      />
    </div>
  );
};

export default PatientWebinarsPage;
