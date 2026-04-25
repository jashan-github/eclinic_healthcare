import PatientsTable from "@/features/app/patients/components/listing/patients-table";
import { usePatients } from "@/features/app/patients/hooks/use-patients";
import { useHeaderStore } from "@/store/use-header-store";
import { useEffect, type FC, type ReactElement } from "react";

const PatientsPage: FC = (): ReactElement => {
  const { setPageTitle } = useHeaderStore();

  const { patients } = usePatients();
  // console.log("patients",patients)
  useEffect(() => {
    setPageTitle(`Patients (${patients.length})`);
  }, [setPageTitle, patients.length]);

  return (
    <div className="p-6 overflow-auto">
      <PatientsTable />
    </div>
  );
};

export default PatientsPage;
