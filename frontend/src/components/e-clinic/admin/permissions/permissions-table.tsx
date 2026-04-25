// components/admin/permissions-table.tsx
import {
  useAdminPermissionServices,
  useUpdatePermissions,
} from "@/hooks/use-admin-permissions-hooks";
import { useEffect, useState } from "react";

interface Permission {
  key: string;
  label: string;
  doctor: boolean;
  staff: boolean;
}
const MODULE_LABELS: Record<string, string> = {
  appointments: "Appointments",
  patients: "Patients",
  payments: "Payments",
  webinars: "Webinars",
  messages: "Messages",
  analytics: "Analytics",
  rx_templates: "Rx Templates",
};

export default function PermissionsTable() {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [staffServiceKeys, setStaffServiceKeys] = useState<string[]>([]);

  const { data } = useAdminPermissionServices();
  const [isDirty, setIsDirty] = useState(false);
  const { mutate, isPending } = useUpdatePermissions();

  useEffect(() => {
    if (!data) return;

    const doctorEntries = Object.entries(data.doctor || {});
    const staffKeys = Object.keys(data.staff || {});
    console.log(doctorEntries);

    const mapped: Permission[] = doctorEntries.map(([key, value]) => ({
      key,
      label: MODULE_LABELS[key] ?? key,
      doctor: Boolean(value),
      staff: Boolean(data.staff?.[key]),
    }));

    setPermissions(mapped);
    setStaffServiceKeys(staffKeys);
  }, [data]);
  const handleToggle = (index: number, role: "doctor" | "staff") => {
    setPermissions((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [role]: !updated[index][role] };
      return updated;
    });
    setIsDirty(true);
  };

  const buildPayload = () => {
    const payload = {
      doctor: {} as Record<string, boolean>,
      staff: {} as Record<string, boolean>,
    };

    permissions.forEach((p) => {
      payload.doctor[p.key] = p.doctor;
      if (staffServiceKeys.includes(p.key)) {
        payload.staff[p.key] = p.staff;
      }
    });

    return payload;
  };

  const handleSave = () => {
    mutate(buildPayload(), {
      onSuccess: () => setIsDirty(false),
    });
  };

  return (
    <div className="w-full mt-8 p-6 bg-white rounded-lg shadow-[6px_7px_20px_0px_#0000001A]">
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h2 className="font-poppins font-semibold text-[20px] leading-[30px] text-[#0F1011]">
            Permissions
          </h2>
          <p className="font-poppins font-normal text-[13px] leading-5 text-[#6B7280]">
            Manage module access for each role
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={!isDirty || isPending}
          className={`px-5 py-2 rounded-md text-sm font-semibold transition-all
    ${
      !isDirty
        ? "bg-gray-200 text-gray-400 cursor-not-allowed"
        : "bg-[#002FD4] text-white hover:bg-[#001FB8]"
    }
  `}
        >
          {isPending ? "Saving..." : "Save Changes"}
        </button>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[800px] border border-[#E4E5ED] rounded-lg overflow-hidden">
          <table className="w-full table-auto border-collapse">
            <thead className="bg-[#E8EEFD]">
              <tr>
                <th className="py-4 px-6 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left first:pl-8">
                  Module
                </th>
                {/* <th className="py-4 px-6 text-center font-poppins font-bold text-[12px] text-[#0F1011]">
                  Admin
                </th> */}
                <th className="py-4 px-6 text-center font-poppins font-bold text-[12px] text-[#0F1011]">
                  Healthcare Provider
                </th>
                <th className="py-4 px-6 text-center font-poppins font-bold text-[12px] text-[#0F1011]">
                  Staff
                </th>
              </tr>
            </thead>

            <tbody className="bg-white divide-y divide-[#E4E5ED]">
              {permissions &&
                permissions.length > 0 &&
                permissions.map((item, index) => (
                  <tr
                    key={item.key}
                    className="hover:bg-[#F9FAFB] transition-colors"
                  >
                    <td className="py-5 px-6 first:pl-8">
                      <span className="font-poppins font-medium text-[13px] text-[#0F1011]">
                        {item.label}
                      </span>
                    </td>

                    {/* Custom Toggle - Admin */}
                    {/* <td className="py-5 px-6">
                    <div className="flex justify-center">
                      <button
                        onClick={() => handleToggle(index, "admin")}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                          item.admin ? "bg-[#002FD4]" : "bg-gray-300"
                        }`}
                      >
                        <span
                          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform ${
                            item.admin ? "translate-x-5" : "translate-x-0.5"
                          }`}
                        />
                      </button>
                    </div>
                  </td> */}

                    {/* Custom Toggle - Doctor */}
                    <td className="py-5 px-6">
                      <div className="flex justify-center">
                        <button
                          onClick={() => handleToggle(index, "doctor")}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                            item.doctor ? "bg-[#002FD4]" : "bg-gray-300"
                          }`}
                        >
                          <span
                            className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform ${
                              item.doctor ? "translate-x-5" : "translate-x-0.5"
                            }`}
                          />
                        </button>
                      </div>
                    </td>

                    {/* Custom Toggle - Staff */}
                    <td className="py-5 px-6">
                      <div className="flex justify-center">
                        {staffServiceKeys &&
                        staffServiceKeys.length > 0 &&
                        staffServiceKeys.includes(item.key) ? (
                          <button
                            disabled={!staffServiceKeys.includes(item.key)}
                            onClick={() => handleToggle(index, "staff")}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                                ${
                                  !staffServiceKeys.includes(item.key)
                                    ? "bg-gray-200 cursor-not-allowed"
                                    : item.staff
                                      ? "bg-[#002FD4]"
                                      : "bg-gray-300"
                                }
                            `}
                          >
                            <span
                              className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-lg transition-transform ${
                                item.staff ? "translate-x-5" : "translate-x-0.5"
                              }`}
                            />
                          </button>
                        ) : (
                          // keeps table alignment clean
                          <span className="text-gray-400 text-xs">—</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
