import InvoiceTable from "@/features/app/staff/components/invoice-table";

export default function BillingContent() {
  // Static data for now

  return (
    <div className="overflow-auto">
      <div className="min-h-screen bg-[#F4F6F9] p-6">
        {/* Welcome Message */}

        <div className="bg-white p-6  rounded-lg shadow-[6px_7px_20px_0px_#0000001A] flex flex-col h-[700px]">
          <div className="font-poppins text-xl font-semibold leading-6 text-[#0F1011]">
            Recent Invoices
          </div>
          <div className="font-poppins text-sm text-slate-500 mt-1 mb-6">
            Loreum ipsum dolor simit
          </div>

          <div className="flex-1 min-h-0">
            <InvoiceTable />
          </div>
        </div>
      </div>
    </div>
  );
}
