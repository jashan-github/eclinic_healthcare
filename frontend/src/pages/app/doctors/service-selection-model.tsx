// src/components/e-clinic/patient/doctors/service-selection-modal.tsx
import { X } from "@phosphor-icons/react";
import type { DoctorService } from "@/services/doctors-service";

interface ServiceSelectionModalProps {
  doctorName: string;
  services: DoctorService[];
  onSelect: (serviceId: DoctorService) => void;
  onClose: () => void;
  formattedFee: string;
}

const ServiceSelectionModal = ({
  doctorName,
  services,
  onSelect,
  onClose,
  // formattedFee,
}: ServiceSelectionModalProps) => {
  const getServiceModeLabel = (mode: string) => {
    switch (mode) {
      case "IN_CLINIC":
        return "In-Clinic";
      case "TELECLINIC":
        return "TeleClinic";
      default:
        return mode;
    }
  };

  const getAppointmentTypeLabel = (type: string) => {
    switch (type) {
      case "REGULAR":
        return "Regular";
      case "FOLLOW_UP":
        return "Follow-up";
      case "EMERGENCY":
        return "Emergency";
      default:
        return type;
    }
  };
  console.log(services);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50   p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#E4E5ED]">
          <div>
            <h2 className="font-poppins font-semibold text-xl text-[#0F1011]">
              Select Service
            </h2>
            <p className="font-poppins text-sm text-[#64748B] mt-1">
              Choose a service to book appointment with {doctorName}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#F4F6F9] rounded-lg transition-colors"
          >
            <X size={24} className="text-[#64748B]" />
          </button>
        </div>

        {/* Services List */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {services.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-[#64748B] font-poppins">
                No services available for this doctor
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {services.map((service) => (
                <div
                  key={service.id}
                  onClick={() => onSelect(service)}
                  className="border border-[#E4E5ED] rounded-lg p-4 hover:border-[#002FD4] hover:bg-[#F4F6F9] cursor-pointer transition-all group"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-poppins font-semibold text-base text-[#0F1011] group-hover:text-[#002FD4]">
                        {service.nickname || service.name}
                      </h3>
                      {service.nickname && (
                        <p className="font-poppins text-sm text-[#64748B] mt-1">
                          {service.name}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="font-poppins font-bold text-lg text-[#002FD4]">
                        {service?.currency} {service?.price}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mt-3">
                    <span className="px-3 py-1 bg-[#E4E1FA] text-[#002FD4] rounded-full text-xs font-medium">
                      {getServiceModeLabel(service.service_mode)}
                    </span>
                    <span className="px-3 py-1 bg-[#F3F5F6] text-[#64748B] rounded-full text-xs font-medium">
                      {getAppointmentTypeLabel(service.appointment_type)}
                    </span>
                    <span className="px-3 py-1 bg-[#F3F5F6] text-[#64748B] rounded-full text-xs font-medium">
                      {service.slot_duration_minutes} min
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ServiceSelectionModal;
