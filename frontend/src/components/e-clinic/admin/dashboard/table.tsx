import { useMemo, useState, type FC, type ReactElement } from "react";
import { Loader } from "@mantine/core";
import HeadSubhead from "@/components/ui/head-subhead";
import { useDashboardActiveAppointments } from "@/hooks/use-dashboard";
import type { ActiveAppointment } from "@/services/dashboard";
import { DownloadSimple } from "@phosphor-icons/react";
import { useDownloadStaffInvoice } from "@/hooks/use-staff";
import { toast } from "react-toastify";

const statusBadge = (s: string) => {
  const upper = s.toUpperCase();
  if (upper === "CONFIRMED")
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[12px] font-semibold bg-[#EAF6FF] text-[#0A66FF]">
        Confirmed
      </span>
    );
  if (upper === "PENDING")
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[12px] font-semibold bg-[#FFF6EA] text-[#FF9200]">
        Pending
      </span>
    );
  if (upper === "CANCELLED")
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[12px] font-semibold bg-[#FEF2F2] text-[#EF4444]">
        Cancelled
      </span>
    );
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[12px] font-semibold bg-[#F4F6F9] text-gray-600">
      {s}
    </span>
  );
};

const formatDate = (iso: string) => {
  const d = new Date(iso);
  const options: Intl.DateTimeFormatOptions = {
    day: "2-digit",
    month: "short",
    year: "numeric",
  };
  return d.toLocaleDateString(undefined, options);
};

const formatTime = (time: string) => {
  const [h, m] = time.split(":");
  const hour = parseInt(h, 10);
  const ampm = hour >= 12 ? "PM" : "AM";
  const display = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
  return `${display}:${m} ${ampm}`;
};

const DataTable: FC = (): ReactElement => {
  const [statusFilter, _] = useState("All");

  const { data, isLoading, isError } = useDashboardActiveAppointments();
  const downloadMutation = useDownloadStaffInvoice();

  const handleDownloadInvoice = (invoiceId: string) => {
    downloadMutation.mutate(invoiceId, {
      onSuccess: () => {
        toast.success("Invoice downloaded successfully");
      },
      onError: (error: any) => {
        toast.error(error?.message || "Failed to download invoice");
      },
    });
  };

  const appointments = data?.data ?? [];

  const filtered = useMemo(() => {
    if (statusFilter === "All") return appointments;
    return appointments.filter(
      (a: ActiveAppointment) => a.status.toUpperCase() === statusFilter,
    );
  }, [statusFilter, appointments]);

  return (
    <section className="w-full">
      <div className="bg-white rounded-2xl p-5 shadow-[6px_7px_20px_0px_#0000001A]">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <HeadSubhead
            head={"Active Appointments"}
            subhead={"Manage appointments and permissions"}
          />
          {/* <div className="flex items-center gap-3 md:gap-4">
            <div className="flex items-center gap-2 bg-[#F4F4F4] w-[150px] h-[39px] px-3 rounded-md border border-transparent">
              <Funnel
                size={16}
                weight="bold"
                className="text-[#0F172A]"
              />
              <Select
                data={statusOptions as unknown as string[]}
                value={statusFilter}
                onChange={(value) =>
                  setStatusFilter(
                    (value ?? 'All') as (typeof statusOptions)[number]
                  )
                }
                rightSection={
                  <CaretDown
                    size={14}
                    weight="bold"
                    className="text-[#0F1011]"
                  />
                }
                classNames={{
                  root: 'flex-1',
                  wrapper: 'flex-1',
                  input:
                    '!bg-transparent !border-none !shadow-none !h-[39px] !px-0 font-poppins !font-bold text-[13px] leading-[16px] text-black cursor-pointer',
                  dropdown:
                    'rounded-lg shadow-md border border-gray-200 font-poppins text-[13px] overflow-visible font-bold',
                  option:
                    'hover:bg-[#F4F6F9] text-black font-poppins font-bold text-[13px] flex items-center justify-between'
                }}
                styles={{
                  dropdown: {
                    minWidth: 120,
                    overflow: 'visible'
                  }
                }}
              />
            </div>
          </div> */}
        </div>

        <div>
          {isLoading ? (
            <div className="flex justify-center items-center py-16">
              <Loader size="sm" />
            </div>
          ) : isError ? (
            <div className="text-center text-[#64748B] py-16">
              Failed to load appointments
            </div>
          ) : (
            <div className="overflow-x-auto">
              <div className="min-w-[900px] border border-[#E4E5ED] rounded-lg overflow-hidden">
                <table className="w-full table-auto border-collapse">
                  <thead className="bg-[#E8EEFD]">
                    <tr className="text-center font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011]">
                      <th className="py-3 px-4">Sr. No.</th>
                      <th className="py-3 px-4">Date & Time</th>
                      <th className="py-3 px-4">Patient Name</th>
                      <th className="py-3 px-4">Doctor</th>
                      <th className="py-3 px-4">Service</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Payment</th>
                      <th className="py-3 px-4">Invoice</th>
                    </tr>
                  </thead>

                  <tbody className="bg-white divide-y divide-[#E4E5ED] font-poppins font-normal text-[13px] leading-[20px] text-[#0F1011] text-center">
                    {filtered.map((a: ActiveAppointment, idx: number) => (
                      <tr key={a.id}>
                        <td className="py-4 px-4">{idx + 1}</td>
                        <td className="py-4 px-4">
                          <div>{formatDate(a.appointment_date)}</div>
                          <div>
                            {formatTime(a.start_time)} –{" "}
                            {formatTime(a.end_time)}
                          </div>
                        </td>
                        <td className="py-4 px-4">{a.patient_name}</td>
                        <td className="py-4 px-4">{a.doctor_name}</td>
                        <td className="py-4 px-4">{a.service_name}</td>
                        <td className="py-4 px-4">{statusBadge(a.status)}</td>
                        <td className="py-4 px-4">
                          {a.currency} {a.price_amount.toLocaleString("en-US")}
                        </td>
                        <td className="py-4 px-4 text-right">
                          <div className="inline-flex items-center gap-3">
                            {a?.invoice_id ? (
                              <button
                                aria-label="download"
                                className="p-2 rounded-full hover:bg-[#F4F6F9]"
                              >
                                <DownloadSimple
                                  size={16}
                                  weight="regular"
                                  onClick={() => {
                                    if (!a?.invoice_id) return;
                                    handleDownloadInvoice(a?.invoice_id);
                                  }}
                                />
                              </button>
                            ) : (
                              "NA"
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {filtered.length === 0 && (
                      <tr>
                        <td
                          colSpan={8}
                          className="py-8 px-4 text-center text-gray-900"
                        >
                          No appointments found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default DataTable;
