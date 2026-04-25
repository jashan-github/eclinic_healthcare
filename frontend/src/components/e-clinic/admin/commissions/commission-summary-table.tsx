// components/e-clinic/admin/commission/monthly-commission-summary.tsx

import type { DateRange } from "react-day-picker";
import { format } from "date-fns";
import { useState } from "react";
import DateRangePicker from "@/components/ui/DateRangePicker";
import { useGetCommissionByDateRange } from "@/hooks/use-admin-comission-rate";

type ServiceCommission = {
  service_id: string;
  service_name: string;
  total_payment_amount: number;
  commission_rate: number | null;
  commission_earned: number;
  payment_count: number;
};
export default function CommissionSummaryTable() {
  const [range, setRange] = useState<DateRange | undefined>();
  const params =
    range?.from && range?.to
      ? {
          date_from: format(range.from, "yyyy-MM-dd"),
          date_to: format(range.to, "yyyy-MM-dd"),
        }
      : undefined;

  const { data, isLoading } = useGetCommissionByDateRange(params);
  const commissionData: ServiceCommission[] = data ?? [];

  return (
    <div className="w-full mt-8 p-6 bg-white rounded-xl shadow-[6px_7px_20px_0px_#0000001A]">
      {/* Header */}
      <div className="mb-6 flex flex-row justify-between">
        <div>
          <h2 className="font-poppins font-semibold text-[20px] leading-[30px] text-[#0F1011]">
            Monthly Commission Summary
          </h2>
          <p className="font-poppins font-normal text-[13px] leading-5 text-[#6B7280]">
            Doctor earnings from commissions
          </p>
        </div>
        <div>
          <DateRangePicker range={range} onChange={setRange} />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <div className="min-w-[800px] border border-[#E4E5ED] rounded-lg overflow-hidden">
          <table className="w-full table-auto border-collapse">
            {/* Table Header */}
            <thead className="bg-[#E8EEFD]">
              <tr>
                {[
                  "Service",
                  "Total Payment",
                  "Commission Rate",
                  "Commission Earned",
                  "Payments",
                ].map((header) => (
                  <th
                    key={header}
                    className="py-4 px-6 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left first:pl-8"
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>

            {/* Table Body */}
            <tbody className="bg-white divide-y divide-[#E4E5ED]">
              {isLoading && (
                <tr>
                  <td colSpan={4} className="py-10 text-center">
                    Loading…
                  </td>
                </tr>
              )}
              {commissionData.map((item) => (
                <tr key={item.service_id}>
                  <td className="py-5 px-6 font-medium">{item.service_name}</td>

                  <td className="py-5 px-6">
                    ₹{item.total_payment_amount.toLocaleString()}
                  </td>

                  <td className="py-5 px-6">
                    {item.commission_rate !== null
                      ? `${item.commission_rate}%`
                      : "—"}
                  </td>

                  <td className="py-5 px-6">
                    ₹{item.commission_earned.toLocaleString()}
                  </td>

                  <td className="py-5 px-6">{item.payment_count}</td>
                </tr>
              ))}

              {/* Empty State (optional) */}
              {!isLoading && commissionData.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-16 text-center text-gray-400">
                    No commission data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
