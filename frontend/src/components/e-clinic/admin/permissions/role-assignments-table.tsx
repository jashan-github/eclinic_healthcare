// components/admin/role-assignments-table.tsx

import { PencilSimple, Trash } from "@phosphor-icons/react";

interface UserRole {
  id: number;
  name: string;
  email: string;
  role: "Admin" | "Healthcare Provider" | "Patient";
}

const usersData: UserRole[] = [
  { id: 1, name: "Admin", email: "admin@gmail.com", role: "Admin" },
  { id: 2, name: "Dr. Sophie Charles", email: "sophiecharles@gmail.com", role: "Healthcare Provider" },
  { id: 3, name: "Tina Parker", email: "tinaparker@gmail.com", role: "Patient" },
  { id: 4, name: "Dr. Nick Williams", email: "nick.williams@clinic.com", role: "Healthcare Provider" },
  { id: 5, name: "Sarah Johnson", email: "sarah.j@clinic.com", role: "Patient" },
];

export default function RoleAssignmentsTable() {
  return (
    <div className="w-full mt-8 p-6 bg-white rounded-xl shadow-[6px_7px_20px_0px_#0000001A]">
      {/* Header */}
      <div className="mb-6">
        <h2 className="font-poppins font-semibold text-[20px] leading-[30px] text-[#0F1011]">
          Role Assignments
        </h2>
        <p className="font-poppins font-normal text-[13px] leading-5 text-[#6B7280]">
          Current role assignments by user
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <div className="min-w-[800px] border border-[#E4E5ED] rounded-lg overflow-hidden">
          <table className="w-full table-auto border-collapse">
            {/* Table Header */}
            <thead className="bg-[#E8EEFD]">
              <tr>
                <th className="py-4 px-6 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left first:pl-8">
                  User
                </th>
                <th className="py-4 px-6 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">
                  Email
                </th>
                <th className="py-4 px-6 text-center font-poppins font-bold text-[12px] text-[#0F1011]">
                  Current Role
                </th>
                <th className="py-4 px-6 text-center font-poppins font-bold text-[12px] text-[#0F1011]">
                  Action
                </th>
              </tr>
            </thead>

            {/* Table Body */}
            <tbody className="bg-white divide-y divide-[#E4E5ED]">
              {usersData.map((user) => (
                <tr key={user.id} className="hover:bg-[#F9FAFB] transition-colors">
                  {/* User Name */}
                  <td className="py-3 px-6 first:pl-8">
                    <span className="font-poppins font-normal text-[13px] text-[#0F1011]">
                      {user.name}
                    </span>
                  </td>

                  {/* Email */}
                  <td className="py-3 px-6">
                    <span className="font-poppins font-normal text-[13px] text-[#0F1011]">
                      {user.email}
                    </span>
                  </td>

                  {/* Current Role Badge */}
                  <td className="py-3 px-6">
                    <div className="flex justify-center">
                      <span
                        className={`inline-flex px-4 py-1.5 rounded-full text-xs font-poppins font-semibold bg-[#002FD41A] text-[#002FD4]`}
                      >
                        {user.role}
                      </span>
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="py-3 px-6">
                    <div className="flex justify-center items-center gap-3">
                      <button
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        aria-label="Edit role"
                      >
                        <PencilSimple size={18} className="text-gray-600" />
                      </button>
                      <button
                        className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                        aria-label="Delete user"
                      >
                        <Trash size={18} className="text-red-500" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {/* Empty State */}
              {usersData.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-16 text-center text-gray-400 font-poppins text-[14px]">
                    No users found.
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