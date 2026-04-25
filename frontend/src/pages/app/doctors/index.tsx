// src/pages/doctors/index.tsx
import {
  CalendarIcon,
  CaretLeftIcon,
  CaretRightIcon,
} from "@phosphor-icons/react";
import { useEffect, useState } from "react";
import { useDoctors } from "@/hooks/use-doctors";
import type { Doctor, DoctorService } from "@/services/doctors-service";
import LoaderCircleAnimated from "@/components/orvo/common/loader-circle-animated";
import BookAppointmentForm from "@/components/e-clinic/patient/doctors/book-appointment/book-appointment-form";
import { useSpecializations } from "@/features/app/my-profile/hooks/use-specializations";
import ServiceSelectionModal from "./service-selection-model";
import { toast } from "react-toastify";
import { useAuth } from "@/context/auth/auth-context-utils";
import HipaaForm from "@/components/e-clinic/patient/hippa-form/hipaa-form";

const DoctorsPage = () => {
  const [selectedSpecialty, setSelectedSpecialty] = useState("");
  const [selectedAvailability, setSelectedAvailability] = useState("Any Time");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [selectedServiceId, setSelectedServiceId] =
    useState<DoctorService | null>(null);
  const [showServiceModal, setShowServiceModal] = useState(false);
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());
  const [shouldFetch, setShouldFetch] = useState(true);
  const [showHipaaModal, setShowHipaaModal] = useState(false);
  const [hipaaFormFilled, setHipaaFormFilled] = useState(false);

  const { specializations, isLoading: loadingSpecs } = useSpecializations();
  const { user, refetchUser } = useAuth();

  const limit = 20;
  const FALLBACK_IMAGE = "/assets/icons/doctor-icon.svg";

  const handleImageError = (doctorId: string) => {
    setImageErrors((prev) => new Set(prev).add(doctorId));
  };

  const getImageSrc = (doctor: Doctor) => {
    return imageErrors.has(doctor.id) ? FALLBACK_IMAGE : doctor.image;
  };

  const formatExperience = (exp: number | string) => {
    if (exp === "N/A") return "N/A";
    const numExp = Number(exp);
    if (isNaN(numExp)) return "N/A";
    return numExp === 1 ? "1 year" : `${numExp} years`;
  };

  const formatRating = (rating: number | string) =>
    rating === "N/A" ? "N/A" : `${rating}/5`;
  const formatFee = (fee: number | string, currency?: string) => {
    if (fee === "N/A") return "N/A";

    const formattedFee = Number(fee).toLocaleString("en-US", {
      minimumFractionDigits: 0,
    });

    if (currency === "INR") {
      return `₹ ${formattedFee}`;
    } else if (currency === "USD") {
      return `$ ${formattedFee}`;
    }

    return `XCG ${formattedFee}`;
  };
  const formatAvailability = (avail: string[]) =>
    avail.includes("N/A") ? "N/A" : avail.join(", ");

  const availabilityOptions = [
    { value: "Any Time", label: "Any Time" },
    { value: "Mon", label: "Monday" },
    { value: "Tue", label: "Tuesday" },
    { value: "Wed", label: "Wednesday" },
    { value: "Thu", label: "Thursday" },
    { value: "Fri", label: "Friday" },
    { value: "Sat", label: "Saturday" },
    { value: "Sun", label: "Sunday" },
  ];

  const apiFilters = {
    specialty_id: selectedSpecialty || undefined,
    availability_day:
      selectedAvailability !== "Any Time" ? selectedAvailability : undefined,
    page: currentPage,
    limit,
    shouldFetch,
  };

  const {
    data: doctorsData,
    isLoading,
    error,
    refetch,
  } = useDoctors(apiFilters);

  const doctors = doctorsData?.doctors || [];
  const totalPages = doctorsData?.totalPages || 1;

  const handleHipaaSuccess = async () => {
    setShowHipaaModal(false);

    // Mark HIPAA as filled locally
    setHipaaFormFilled(true);

    // Refetch user data in background
    await refetchUser?.();

    // Open service modal
    if (selectedDoctor) {
      setShowServiceModal(true);
    }
  };

  const handleApplyFilters = () => {
    setCurrentPage(1);
    setShouldFetch(true);
    refetch();
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    setShouldFetch(true);
    refetch();
  };

  // Handle Book Appointment button click
  const handleBookAppointment = (doctor: Doctor) => {
    if (doctor.services.length === 0) {
      toast.error("No services available for this healthcare provider");
      return;
    }

    // Check HIPAA status - use local state OR user data
    const isHipaaFilled = hipaaFormFilled || (user && user.hipaa_form_filled);

    if (!isHipaaFilled) {
      setSelectedDoctor(doctor);
      setShowHipaaModal(true);
      return;
    }

    // If HIPAA form is already filled, show service modal directly
    setSelectedDoctor(doctor);
    setShowServiceModal(true);
  };

  // Handle service selection from modal
  const handleServiceSelect = (serviceId: DoctorService) => {
    setSelectedServiceId(serviceId);
    setShowServiceModal(false);
  };

  // Handle modal close
  const handleCloseServiceModal = () => {
    setShowServiceModal(false);
    setSelectedDoctor(null);
  };

  // Handle back from booking form
  const handleBackFromBooking = () => {
    setSelectedDoctor(null);
    setSelectedServiceId(null);
  };

  // Add this useEffect after your other state declarations
  useEffect(() => {
    if (user?.hipaa_form_filled) {
      setHipaaFormFilled(true);
    }
  }, [user]);

  // Show booking form when both doctor and service are selected
  if (selectedDoctor && selectedServiceId && !showServiceModal) {
    return (
      <BookAppointmentForm
        doctorId={selectedDoctor.id}
        doctor={selectedDoctor}
        serviceId={selectedServiceId}
        onBack={handleBackFromBooking}
        onImageError={handleImageError}
        getImageSrc={getImageSrc}
        formatExperience={formatExperience}
        formatRating={formatRating}
        formatFee={formatFee}
        calculateTotal={(fee, intake) =>
          fee === "N/A" ? "N/A" : Number(fee) + intake
        }
      />
    );
  }

  return (
    <div className="bg-[#F4F6F9] p-6">
      <p className="font-poppins font-medium text-lg leading-6 text-[#0F1011] mb-6">
        Browse our network of qualified healthcare professionals
      </p>

      {/* Filter Section */}
      <div className="bg-white rounded-lg border border-[#E4E5ED] p-6 mb-6">
        <h2 className="font-poppins font-medium text-xl leading-6 text-[#0F1011] mb-4">
          Filter Healthcare Providers
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 items-end">
          {/* Specialty */}
          <div>
            <label className="block mb-2 font-poppins font-semibold text-sm leading-5 text-[#0F1011]">
              Specialty
            </label>
            <select
              value={selectedSpecialty}
              onChange={(e) => setSelectedSpecialty(e.target.value)}
              disabled={loadingSpecs}
              className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] font-poppins text-sm font-normal text-[#0F1011] leading-5 focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] disabled:opacity-50"
            >
              <option value="">All Specialties</option>
              {loadingSpecs ? (
                <option>Loading...</option>
              ) : (
                specializations?.map((spec: any) => (
                  <option key={spec.id} value={spec.id}>
                    {spec.name}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Availability */}
          <div>
            <label className="block mb-2 font-poppins font-semibold text-sm leading-5 text-[#0F1011]">
              Availability
            </label>
            <select
              value={selectedAvailability}
              onChange={(e) => setSelectedAvailability(e.target.value)}
              className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
    font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
    focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
            >
              {availabilityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Apply Filters Button */}
          <button
            onClick={handleApplyFilters}
            className="sm:col-span-2 lg:col-span-1 w-full text-[#002FD4] border border-[#E4E1FA]
      font-poppins font-bold text-sm leading-5 py-2.5 px-6 rounded-md
      hover:bg-[#F4F6F9] transition-colors whitespace-nowrap"
          >
            Apply Filters
          </button>
        </div>
      </div>

      {/* Doctor Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-8">
        {isLoading ? (
          <div className="col-span-full text-center py-12">
            <LoaderCircleAnimated />
          </div>
        ) : error ? (
          error.message === "Fetch not triggered" ? (
            <div className="col-span-full text-center py-12">
              <p className="text-[#64748B] font-poppins text-lg">
                Apply filters to search healthcare providers
              </p>
            </div>
          ) : (
            <div className="col-span-full text-center py-12">
              <p className="text-red-500 font-poppins text-lg">
                Failed to load healthcare providers. Please try again.
              </p>
              <button
                onClick={handleApplyFilters}
                className="mt-4 bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold 
          text-[14px] leading-[20px] py-2.5 px-6 rounded-md transition-colors"
              >
                Retry
              </button>
            </div>
          )
        ) : doctors.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <p className="text-[#64748B] font-poppins text-lg">
              No healthcare providers found
            </p>
          </div>
        ) : (
          doctors.map((doctor) => (
            <div
              key={doctor.id}
              className="bg-white rounded-lg border border-[#E4E5ED] p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex justify-center mb-4">
                <img
                  src={getImageSrc(doctor)}
                  alt={doctor.name}
                  onError={() => handleImageError(doctor.id)}
                  className="w-[120px] h-[120px] rounded-full object-cover border-4 border-[#F4F6F9]"
                />
              </div>

              <h3 className="font-poppins font-medium text-xl text-center mb-2">
                {doctor.name}
              </h3>
              <p className="font-poppins font-semibold text-xs text-center text-[#002FD4] mb-3">
                {doctor.specialty}
              </p>

              <div className="flex justify-center gap-2 mb-4 flex-wrap">
                {doctor.degrees.map((d, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-[#F3F5F6] rounded-full text-[12px] font-medium"
                  >
                    {d}
                  </span>
                ))}
              </div>

              <div className="border-t border-[#E4E5ED] mb-4"></div>

              <div className="flex justify-between mb-3">
                <p className="text-[14px] mb-3">
                  <span className="text-[#002FD4] font-semibold">
                    {formatFee(doctor.consultationFee, doctor.currency)}
                  </span>{" "}
                  consultation fee
                </p>
                <p className="text-[14px] text-[#64748B]">
                  {formatExperience(doctor.experience)} experience
                </p>
              </div>

              <div className="flex items-center gap-2 mb-4">
                <CalendarIcon
                  size={16}
                  weight="bold"
                  className="text-[#002FD4]"
                />
                <span className="text-[14px]">
                  Available: {formatAvailability(doctor.availability)}
                </span>
              </div>

              <button
                onClick={() => handleBookAppointment(doctor)}
                className="w-full border-2 border-[#002FD4] text-[#002FD4] font-bold py-2.5 rounded-md hover:bg-[#F4F6F9] transition-colors"
              >
                Book Appointment
              </button>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-8">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="p-2 disabled:text-gray-400"
          >
            <CaretLeftIcon size={20} />
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button
              key={page}
              onClick={() => handlePageChange(page)}
              className={`px-4 py-2 rounded ${currentPage === page ? "bg-[#002FD4] text-white" : "text-[#64748B] hover:text-[#002FD4]"}`}
            >
              {page}
            </button>
          ))}

          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="p-2 disabled:text-gray-400"
          >
            <CaretRightIcon size={20} />
          </button>
        </div>
      )}

      {/* Service Selection Modal */}
      {showServiceModal && selectedDoctor && (
        <ServiceSelectionModal
          doctorName={selectedDoctor.name}
          services={selectedDoctor.services}
          onSelect={handleServiceSelect}
          onClose={handleCloseServiceModal}
          formattedFee={formatFee(
            selectedDoctor.consultationFee,
            selectedDoctor.currency,
          )}
        />
      )}

      {showHipaaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* backdrop */}
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setShowHipaaModal(false)}
          />

          {/* modal */}
          <div className="relative z-10">
            <HipaaForm
              onClose={() => setShowHipaaModal(false)}
              onSuccess={handleHipaaSuccess}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DoctorsPage;
