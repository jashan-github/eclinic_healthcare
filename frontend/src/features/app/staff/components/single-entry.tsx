// single-entry.tsx

import { useState } from "react";
import {
  Phone,
  EnvelopeSimple,
  VideoCameraIcon,
  MapPinIcon,
  ClockIcon,
  UserIcon,
  CheckCircleIcon,
  CalendarBlankIcon,
  CurrencyDollarIcon, // ADD
  StethoscopeIcon,
} from "@phosphor-icons/react";
import { Modal, Loader } from "@mantine/core";
import { usePatientContactDetails } from "@/hooks/use-staff";

interface SingleEntryProps {
  date: string;
  name: string;
  email: string;
  type: "Teleconsultation" | "In-Clinic";
  time: string;
  doctor: string;
  duration: number;
  status: "Confirmed" | "Pending";
  paymentStatus: "Paid" | "Unpaid" | "Refunded";
  paymentMethod?: string;
  contactNumber: string;
  emergencyContact: string;
  familyContact: string;
  patientId: string;
  serviceName: string; // ADD
  amount: string;
}

const SingleEntry: React.FC<SingleEntryProps> = ({
  date,
  name,
  email,
  type,
  time,
  doctor,
  duration,
  status,
  paymentStatus,
  paymentMethod,
  contactNumber,
  emergencyContact,
  familyContact,
  patientId,
  serviceName, // ADD
  amount,
}) => {
  const [isContactOpen, setIsContactOpen] = useState(false);

  // Fetch contact details when modal opens
  const {
    data: contactData,
    isLoading: isLoadingContact,
    error: contactError,
  } = usePatientContactDetails(
    patientId,
    isContactOpen, // Only fetch when modal is open
  );

  // First letter of name for avatar
  const avatarLetter = name.charAt(0).toUpperCase();

  // Final display text
  const paymentDisplay = paymentMethod
    ? `${paymentStatus} (${paymentMethod})`
    : paymentStatus;

  return (
    <div className="bg-white rounded-lg border border-gray-100 p-6 space-y-4">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 bg-[#E8EEFD] rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-[#002FD4] font-bold text-lg">
            {avatarLetter}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="font-poppins text-lg font-semibold leading-7 text-[#0F1011] align-middle">
              {name}
            </h2>
          </div>

          <div className="flex flex-wrap items-center gap-6 my-2">
            <div className="flex items-center gap-2">
              <StethoscopeIcon size={18} color="#002FD4" />
              <span className="font-poppins text-sm font-semibold text-[#0F1011]">
                {serviceName}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <CurrencyDollarIcon size={18} color="#002FD4" />
              <span className="font-poppins text-sm font-semibold text-[#002FD4]">
                {amount}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {type === "In-Clinic" ? (
                <MapPinIcon size={18} color="#002FD4" />
              ) : (
                <VideoCameraIcon size={18} color="#002FD4" />
              )}
              <span className="font-poppins text-sm font-medium text-gray-700">
                {type}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-6 flex-wrap">
            <div className="flex items-center gap-2">
              <ClockIcon size={20} color="#002FD4" />
              <span className="font-poppins text-sm font-normal leading-5 capitalize text-[#0F1011]">
                {time}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <UserIcon size={20} color="#002FD4" />
              <span className="font-poppins text-sm font-normal leading-5 capitalize text-[#0F1011]">
                {doctor}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <CalendarBlankIcon size={20} color="#002FD4" />
              <span className="font-poppins text-sm font-normal leading-5 text-[#0F1011]">
                {date}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-6 mt-2">
            <span className="font-poppins text-sm font-semibold leading-5 text-[#0F1011] align-middle">
              Duration: {duration} min
            </span>
            <span className="font-poppins text-sm font-semibold leading-5 text-[#0F1011] align-middle">
              Payment Status: {paymentDisplay}
            </span>
          </div>
        </div>

        <div className="flex flex-col justify-center gap-12 h-full">
          <div
            className={`inline-flex items-center gap-1 w-fit px-2 rounded-full font-medium text-sm ${
              status === "Confirmed"
                ? "bg-[#E8EEFD] text-[#002FD4]"
                : "bg-orange-50 text-orange-700 border-orange-200"
            }`}
          >
            {status === "Confirmed" ? (
              <CheckCircleIcon size={18} weight="fill" className="#002FD4" />
            ) : (
              <ClockIcon size={18} weight="fill" className="text-orange-600" />
            )}

            <span>{status}</span>
          </div>
          <div
            onClick={() => setIsContactOpen(true)}
            className="w-full cursor-pointer transition-colors"
          >
            <span className="font-poppins text-sm font-medium leading-5 text-center block underline text-slate-600 align-middle">
              Contact Details
            </span>
          </div>
        </div>
      </div>

      <Modal
        opened={isContactOpen}
        onClose={() => setIsContactOpen(false)}
        title={
          <div className="flex items-center justify-between w-full">
            <span className="font-poppins text-base font-bold leading-6 text-[#0F1011]">
              Patient Contact Details
            </span>
          </div>
        }
        size="580px"
        radius={"lg"}
        centered
        styles={{
          header: {
            borderBottom: "none",
            paddingBottom: 0,
            paddingLeft: "2rem",
            paddingRight: "2rem",
          },
          body: {
            paddingTop: 0,
          },
        }}
      >
        <div className="p-6 space-y-6">
          {isLoadingContact ? (
            <div className="flex items-center justify-center py-10">
              <Loader size="md" />
            </div>
          ) : contactError ? (
            <div className="text-center py-10 text-red-500 font-medium">
              Failed to load contact details. Please try again.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <UserIcon size={18} className="text-[#002FD4]" />
                    <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                      Full Name
                    </span>
                  </label>
                  <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle ml-6">
                    {contactData?.data?.full_name || name || "N/A"}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <EnvelopeSimple
                      size={18}
                      weight="duotone"
                      className="text-[#002FD4]"
                    />
                    <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                      Email
                    </span>
                  </label>
                  <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle ml-6">
                    {contactData?.data?.email || email || "N/A"}
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg p-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <label className="flex items-center gap-2">
                      <Phone
                        size={18}
                        weight="duotone"
                        className="text-[#002FD4]"
                      />
                      <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                        Contact
                      </span>
                    </label>
                    <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle ml-6">
                      {contactData?.data?.contact || contactNumber || "N/A"}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                      Emergency Contact
                    </span>
                    <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle mt-1">
                      {contactData?.data?.emergency_contact ||
                        emergencyContact ||
                        "N/A"}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <span className="font-poppins text-sm font-medium leading-5 text-[#0F1011] align-middle">
                      Family Contact
                    </span>
                    <div className="font-poppins text-sm font-medium leading-5 text-[#A5ABB3D9] align-middle mt-1">
                      {contactData?.data?.family_contact ||
                        familyContact ||
                        "N/A"}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default SingleEntry;
