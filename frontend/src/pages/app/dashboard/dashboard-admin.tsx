import FourCards from "@/components/e-clinic/admin/dashboard/four-data-cards";
import DataTable from "@/components/e-clinic/admin/dashboard/table";
import TwoCards from "@/components/e-clinic/admin/dashboard/two-data-cards";
import Welcome from "@/components/e-clinic/admin/dashboard/welcome-header";

export default function AdminDashboard() {
  return (
    <div className="min-h-screen">
      <div className="bg-[#F4F6F9] space-y-10 p-4">
        {/* Welcome header */}
        <Welcome />

        {/* 4 Data Cards */}
        <FourCards />

        {/* 2 Data Cards */}
        <TwoCards />

        {/* Table */}
        <DataTable />
      </div>
    </div>
  )
}
