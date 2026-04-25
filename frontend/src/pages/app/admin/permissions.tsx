import PermissionsCards from "@/components/e-clinic/admin/permissions/permissions-cards";
import PermissionsTable from "@/components/e-clinic/admin/permissions/permissions-table";
import RoleAssignmentsTable from "@/components/e-clinic/admin/permissions/role-assignments-table";
import HeadSubhead from "@/components/ui/head-subhead";
import { type FC, type ReactElement } from "react";

const PermissionsPage: FC = (): ReactElement => {
  return (
    <>
      <div className="h-full bg-[#F4F6F9] overflow-auto">
        <div className="p-4 h-full">
          <div className="flex justify-between items-center p-6">
            <HeadSubhead
              head={"Advanced Analytics"}
              subhead={
                "Comprehensive insights into revenue, appointments, and webinars"
              }
            />
          </div>
          <div className="p-4">
            <PermissionsCards />
          </div>
          <div className="p-4">
            <PermissionsTable />
          </div>
          <div className="p-4">
            <RoleAssignmentsTable />
          </div>
        </div>
      </div>
    </>
  );
};

export default PermissionsPage;
