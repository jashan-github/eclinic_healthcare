import {
  CaretDown,
  Funnel,
  MagnifyingGlassIcon,
  PencilIcon,
  TrashIcon,
} from "@phosphor-icons/react";
import { useMemo, useState } from "react";
import {
  useServices,
  useDeleteAdminService,
} from "@/hooks/use-admin-service-hooks";
import CreateNewService from "../../doctor/calendar/create-new-service";
import ConfirmationModal from "@/components/ui/confirmation-modal";
import { Loader } from "@mantine/core";

export default function ServicesTable() {
  const { data: services = [], isLoading, isError } = useServices();

  console.log(services);

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<
    "All" | "Active" | "Inactive"
  >("All");
  const [isServiceModalOpen, setIsServiceModalOpen] = useState(false);
  const [serviceId, setServiceId] = useState<string | undefined>(undefined);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [serviceToDelete, setServiceToDelete] = useState<string | null>(null);
  const [serviceToDeleteName, setServiceToDeleteName] = useState<string>("");

  const deleteServiceMutation = useDeleteAdminService();

  const filteredData = useMemo(() => {
    if (!services || !Array.isArray(services) || services.length === 0)
      return [];
    return services.filter((service) => {
      if (!service) return false;
      const serviceName = (service.serviceName || "").toString();
      const searchTermLower = (searchTerm || "").toString().toLowerCase();
      const matchesSearch = serviceName.toLowerCase().includes(searchTermLower);
      const matchesStatus =
        statusFilter === "All" || service.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [services, searchTerm, statusFilter]);

  const handleEditClick = (serviceId: string) => {
    setServiceId(serviceId);
    setIsServiceModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsServiceModalOpen(false);
    setServiceId(undefined);
  };

  const handleDeleteClick = (serviceId: string, serviceName: string) => {
    setServiceToDelete(serviceId);
    setServiceToDeleteName(serviceName);
    setIsDeleteModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (serviceToDelete) {
      deleteServiceMutation.mutate(serviceToDelete, {
        onSuccess: () => {
          setIsDeleteModalOpen(false);
          setServiceToDelete(null);
          setServiceToDeleteName("");
        },
      });
    }
  };

  const handleCancelDelete = () => {
    setIsDeleteModalOpen(false);
    setServiceToDelete(null);
    setServiceToDeleteName("");
  };

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <Loader />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="w-full mt-4 text-center py-12 text-red-500 font-poppins">
        Error loading services. Please try again later.
      </div>
    );
  }

  return (
    <div className="w-full mt-4">
      <div className="flex flex-row gap-4 mb-6 items-center">
        <div className="relative flex-1">
          <MagnifyingGlassIcon
            color="black"
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5"
          />
          <input
            type="text"
            placeholder="Search by Service Name"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md 
                                   focus:outline-none focus:ring-2 focus:ring-[#002FD4]
                                   font-poppins font-normal text-[14px] leading-[100%] 
                                   text-black placeholder:text-[#A5ABB3]"
          />
        </div>

        <div className="relative">
          <div className="flex items-center gap-2 bg-[#F4F4F4] w-[150px] h-[39px] px-3 rounded-md border border-transparent hover:border-gray-300 transition-all cursor-pointer">
            <Funnel size={16} weight="bold" className="text-[#0F172A]" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            >
              <option value="All">All Status</option>
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
            <span className="flex-1 font-poppins font-bold text-[13px] leading-4 text-black text-center">
              {statusFilter === "All" ? "All Status" : statusFilter}
            </span>
            <CaretDown size={14} weight="bold" className="text-[#0F1011]" />
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[900px] border border-[#E4E5ED] rounded-lg overflow-hidden">
          <table className="w-full table-auto border-collapse">
            <thead className="bg-[#E8EEFD]">
              <tr>
                {[
                  "Sr. No.",
                  "Service Name",
                  "Price",
                  "Type",
                  "Status",
                  "Actions",
                ].map((header) => (
                  <th
                    key={header}
                    className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left"
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody className="bg-white divide-y divide-[#E4E5ED] font-poppins font-normal text-[13px] leading-[20px] text-[#0F1011]">
              {filteredData.map((service, idx) => {
                if (!service || !service.id) return null;
                const serviceName = String(
                  service.serviceName || "Unnamed Service",
                );

                const servicePrice = String(service.price || "XCG 0");

                const serviceType = String(service.type || "N/A");
                const serviceStatus = service.status || "Inactive";
                const currency = service.currency;

                return (
                  <tr
                    key={service.id}
                    className="hover:bg-[#F4F6F9] transition-colors"
                  >
                    <td className="py-4 px-4">{idx + 1}</td>
                    <td className="py-4 px-4 font-medium">{serviceName}</td>
                    <td className="py-4 px-4">
                      {currency} {servicePrice}
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-poppins font-normal text-[13px] leading-5 align-middle text-[#0F1011]">
                        {serviceType}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span
                        className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                          serviceStatus === "Active"
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {serviceStatus}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => handleEditClick(service.id)}
                          className="p-2 rounded-full hover:bg-[#F4F6F9] transition-colors"
                          title="Edit Service"
                        >
                          <PencilIcon
                            size={16}
                            weight="regular"
                            className="text-gray-600"
                          />
                        </button>
                        <button
                          onClick={() =>
                            handleDeleteClick(service.id, serviceName)
                          }
                          className="p-2 rounded-full hover:bg-red-50 transition-colors"
                          title="Delete Service"
                          disabled={deleteServiceMutation.isPending}
                        >
                          <TrashIcon
                            size={16}
                            weight="regular"
                            className="text-gray-600 hover:text-red-600"
                          />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}

              {filteredData.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="py-12 text-center text-gray-400 font-poppins"
                  >
                    No services found matching your criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      <CreateNewService
        isOpen={isServiceModalOpen}
        setIsOpen={handleCloseModal}
        serviceId={serviceId}
      />
      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Service"
        message={`Are you sure you want to delete "${serviceToDeleteName}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonColor="danger"
        isLoading={deleteServiceMutation.isPending}
      />
    </div>
  );
}
