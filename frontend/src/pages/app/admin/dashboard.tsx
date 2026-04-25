import FourCards from "@/components/e-clinic/admin/dashboard/four-data-cards";
import DataTable from "@/components/e-clinic/admin/dashboard/table";
import TwoCards from "@/components/e-clinic/admin/dashboard/two-data-cards";
import Welcome from "@/components/e-clinic/admin/dashboard/welcome-header";
import { type FC, type ReactElement } from "react";

const DashboardPage: FC = (): ReactElement => {
  return (
    <div className="min-h-screen">
      <div className="bg-[#F4F6F9] space-y-4 p-4">
        <Welcome />

        <FourCards />

        <TwoCards />

        <DataTable />
      </div>
    </div>
  );
};

export default DashboardPage;
