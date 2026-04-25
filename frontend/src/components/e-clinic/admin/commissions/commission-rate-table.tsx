// components/e-clinic/admin/commission/commissions-rate-table.tsx

import {
  useDeleteCommission,
  useGetCommissions,
} from "@/hooks/use-admin-comission-rate";
import {
  MagnifyingGlassIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
} from "@phosphor-icons/react";
import { useMemo, useState } from "react";
import EditCommissionModal from "./comission-edit-modal";

export type Commission = {
  id: string;
  service_id: string;
  service_name: string;
  rate: number;
  status: "ACTIVE" | "INACTIVE";
};

export default function CommissionsRateTable() {
  const [searchTerm, setSearchTerm] = useState("");
  const { data = [] } = useGetCommissions();
  const [open, setOpen] = useState(false);
  const [selectedServiceId, setSelectedServiceId] = useState<string | null>(
    null,
  );
  const [mode, setMode] = useState<"create" | "edit">("create");
  const { mutate } = useDeleteCommission();

  const filteredData = useMemo(() => {
    return data.filter((item: any) =>
      item.service_name.toLowerCase().includes(searchTerm.toLowerCase()),
    );
  }, [data, searchTerm]);
  return (
    <div className="bg-white w-full mt-6 p-6 rounded-xl shadow-[6px_7px_20px_0px_#0000001A] min-h-[360px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="font-poppins font-semibold text-[20px] leading-[30px] text-[#0F1011]">
            Commission Rates
          </h2>
          <p className="font-poppins font-normal text-[13px] leading-5 text-[#6B7280]">
            Active commission rates by role and service type
          </p>
        </div>

        <button
          onClick={() => {
            setSelectedServiceId(null);
            setMode("create");
            setOpen(true);
          }}
          className="flex items-center border-[#002FD4] border gap-2 px-4 py-2.5 rounded-md"
        >
          <PlusIcon weight="bold" size={16} color="#002FD4" />
          <span className="font-poppins font-semibold text-[13px] leading-5 text-center text-[#002FD4]">
            Add Commission Rate
          </span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5">
            <MagnifyingGlassIcon size={18} color="black" />
          </div>
          <input
            type="text"
            placeholder="Search by name"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-md 
                       focus:outline-none focus:ring-2 focus:ring-[#002FD4]
                       font-poppins font-normal text-[14px] text-black placeholder:text-[#A5ABB3]"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <div className="min-w-[900px] border border-[#E4E5ED] rounded-lg overflow-hidden">
          <table className="w-full table-auto border-collapse">
            <thead className="bg-[#E8EEFD]">
              <tr>
                {["Sr. No.", "Service Name", "Rate", "Status", "Actions"].map(
                  (header) => (
                    <th
                      key={header}
                      className="py-4 px-6 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left first:pl-8"
                    >
                      {header}
                    </th>
                  ),
                )}
              </tr>
            </thead>

            <tbody className="bg-white divide-y divide-[#E4E5ED]">
              {filteredData.map((item: any, idx: number) => (
                <tr
                  key={item.id}
                  className="hover:bg-[#F9FAFB] transition-colors"
                >
                  <td className="py-5 px-6 first:pl-8">{idx + 1}</td>

                  <td className="py-5 px-6 font-medium">{item.service_name}</td>

                  <td className="py-5 px-6">
                    <span className="font-semibold text-[#002FD4]">
                      {item.rate}%
                    </span>
                  </td>

                  <td className="py-5 px-6">
                    <span
                      className={`inline-flex px-4 py-1.5 rounded-full text-xs font-semibold
            ${
              item.status === "ACTIVE"
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-600"
            }`}
                    >
                      {item.status}
                    </span>
                  </td>

                  <td className="py-5 px-6">
                    <div className="flex items-center">
                      <button
                        className="p-2 rounded-full hover:bg-[#E8EEFD]"
                        onClick={() => {
                          setSelectedServiceId(item.service_id);
                          setMode("edit");
                          setOpen(true);
                        }}
                      >
                        <PencilIcon size={16} />
                      </button>
                      <button
                        className="p-2 rounded-full hover:bg-[#E8EEFD]"
                        onClick={() => {
                          mutate(item.service_id);
                        }}
                      >
                        <TrashIcon size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {filteredData.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-16 text-center text-gray-400">
                    No commission rates found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      <EditCommissionModal
        open={open}
        mode={mode}
        serviceId={selectedServiceId}
        onClose={() => {
          setOpen(false);
          setSelectedServiceId(null);
        }}
      />
    </div>
  );
}
