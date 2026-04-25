import {
  CaretDown,
  Funnel,
  MagnifyingGlassIcon,
  PencilIcon,
  TrashIcon,
  X,
} from "@phosphor-icons/react";
import { useEffect, useMemo, useState } from "react";
import { useUsers, useDeleteUser } from "@/hooks/use-admin-user-hooks";
import { Select } from "@mantine/core";
import AddUserDialog from "./add-user-dialog";
import ConfirmationModal from "@/components/ui/confirmation-modal";
import { Loader } from "@mantine/core";
import { CheckIcon } from "@phosphor-icons/react";

export default function UsersTable() {
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState(searchTerm);
  const [statusFilter, setStatusFilter] = useState<
    "All" | "Active" | "Inactive"
  >("All");
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const perPage = 15;
  const [roleFilter, setRoleFilter] = useState<
    "All" | "Doctor" | "Patient" | "Admin" | "super_admin" | "staff"
  >("All");
  const { data, isLoading, isError } = useUsers(
    currentPage,
    perPage,
    roleFilter,
    debouncedSearchTerm,
  );
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<string | null>(null);
  const [userToDeleteName, setUserToDeleteName] = useState<string>("");

  const deleteUserMutation = useDeleteUser();

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
      setCurrentPage(1); // reset pagination on new search
    }, 400); // 300–500ms is sane

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleEdit = (userId: string) => {
    setSelectedUserId(userId);
    setIsUserModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsUserModalOpen(false);
    setSelectedUserId(null);
  };

  useEffect(() => {
    setCurrentPage(1);
  }, [roleFilter]);

  const usersData = useMemo(() => {
    if (!data?.users || !Array.isArray(data.users)) return [];
    return data.users.map((user) => {
      // Map role from API format to display format
      const roleMap: Record<
        string,
        "Healthcare Provider" | "Patient" | "Staff" | "Admin" | "Staff"
      > = {
        doctor: "Healthcare Provider",
        patient: "Patient",
        staff: "Staff",
        clinic_admin: "Admin",
        super_admin: "Admin",
      };

      const displayRole = roleMap[user.role?.toLowerCase()] || "Patient";
      const nameParts = (user.name || "").split(" ").filter(Boolean);
      const initials =
        nameParts.length > 0
          ? nameParts
              .map((n: string) => n[0])
              .join("")
              .toUpperCase()
              .slice(0, 2)
          : "U";

      return {
        id: user.id,
        initials,
        name: user.name || "Unknown",
        email: user.email || "-",
        contact: user.phone || "-",
        role: displayRole,
        status: user.status || user.is_active ? "Active" : "Inactive",
      };
    });
  }, [data]);

  const filteredData = useMemo(() => {
    return usersData.filter((user) => {
      const matchesSearch = user.name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const matchesStatus =
        statusFilter === "All" || user.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [searchTerm, statusFilter, usersData]);

  const handleDeleteClick = (id: string, name: string) => {
    setUserToDelete(id);
    setUserToDeleteName(name);
    setIsDeleteModalOpen(true);
  };

  const handleConfirmDelete = () => {
    if (userToDelete) {
      deleteUserMutation.mutate(userToDelete, {
        onSuccess: () => {
          setIsDeleteModalOpen(false);
          setUserToDelete(null);
          setUserToDeleteName("");
        },
      });
    }
  };

  const handleCancelDelete = () => {
    setIsDeleteModalOpen(false);
    setUserToDelete(null);
    setUserToDeleteName("");
  };

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <Loader />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="w-full mt-4 text-center py-12 text-red-500 font-poppins">
        Error loading users. Please try again later.
      </div>
    );
  }

  return (
    <>
      <div className="w-full mt-4">
        <div className="flex flex-col sm:flex-row gap-4 mb-6 items-center">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by Name"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 ${searchTerm ? "pr-10" : "pr-4"} py-2 border border-gray-300 rounded-md 
                       focus:outline-none focus:ring-2 focus:ring-[#002FD4]
                       font-poppins font-normal text-[14px] leading-[100%] 
                       text-black placeholder:text-[#A5ABB3]`}
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm("")}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-[#F4F6F9] rounded-md transition-colors"
                title="Clear search"
              >
                <X
                  size={16}
                  weight="bold"
                  className="text-gray-400 hover:text-gray-600"
                />
              </button>
            )}
          </div>
          <div className="flex items-center gap-3 md:gap-4">
            {/* ── NEW Role dropdown ──────────────────────────────────────── */}
            <div className="flex items-center gap-2 bg-[#F4F4F4] w-[200px] h-[39px] px-3 rounded-md border border-transparent">
              <Funnel
                size={16}
                weight="bold"
                className="text-[#0F172A] flex-shrink-0"
              />

              <Select
                data={[
                  { value: "All", label: "All Roles" },
                  { value: "Doctor", label: "Healthcare Provider" },
                  { value: "Patient", label: "Patient" },
                  { value: "Admin", label: "Admin" },
                  { value: "staff", label: "Staff" },
                ]}
                value={roleFilter}
                onChange={(value) =>
                  setRoleFilter(
                    value as
                      | "All"
                      | "Doctor"
                      | "Patient"
                      | "Admin"
                      | "super_admin",
                  )
                }
                rightSection={
                  <CaretDown
                    size={14}
                    weight="bold"
                    className="text-[#0F1011] pointer-events-none"
                  />
                }
                classNames={{
                  root: "flex-1",
                  wrapper: "flex-1",
                  input:
                    "!bg-transparent !border-none !shadow-none !h-[39px] !pl-0 !pr-10 font-poppins !font-bold text-[13px] leading-[16px] text-black cursor-pointer truncate text-ellipsis overflow-hidden whitespace-nowrap",
                  // ↑ Important: !pr-10 gives space for caret, truncate + whitespace-nowrap forces ellipsis
                  dropdown:
                    "rounded-lg shadow-md border border-gray-200 font-poppins text-[13px] overflow-visible font-bold",
                  option:
                    "hover:bg-[#F4F6F9] text-black font-poppins font-bold text-[13px] flex items-center justify-between px-3 py-2",
                }}
                styles={{
                  dropdown: { minWidth: 200, overflow: "visible" },
                }}
                renderOption={({ option, checked }) => (
                  <div className="flex items-center justify-between w-full px-2">
                    <span>{option.label}</span>
                    {checked && (
                      <CheckIcon
                        size={16}
                        weight="light"
                        className="text-[#002FD4]"
                      />
                    )}
                  </div>
                )}
              />
            </div>
          </div>
          {/* ───────────────────────────────────────────────────────────── */}

          <div className="flex items-center gap-3 md:gap-4">
            <div className="flex items-center gap-2 bg-[#F4F4F4] w-[150px] h-[39px] px-3 rounded-md border border-transparent">
              <Funnel size={16} weight="bold" className="text-[#0F172A]" />
              <Select
                data={[
                  { value: "All", label: "All Status" },
                  { value: "Active", label: "Active" },
                  { value: "Inactive", label: "Inactive" },
                ]}
                value={statusFilter}
                onChange={(value) =>
                  setStatusFilter(value as "All" | "Active" | "Inactive")
                }
                rightSection={
                  <CaretDown
                    size={14}
                    weight="bold"
                    className="text-[#0F1011]"
                  />
                }
                classNames={{
                  root: "flex-1",
                  wrapper: "flex-1",
                  input:
                    "!bg-transparent !border-none !shadow-none !h-[39px] !px-0 font-poppins !font-bold text-[13px] leading-[16px] text-black cursor-pointer",
                  dropdown:
                    "rounded-lg shadow-md border border-gray-200 font-poppins text-[13px] overflow-visible font-bold",
                  option:
                    "hover:bg-[#F4F6F9] text-black font-poppins font-bold text-[13px] flex items-center justify-between",
                }}
                styles={{
                  dropdown: {
                    minWidth: 120,
                    overflow: "visible",
                  },
                }}
              />
            </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          <div className="min-w-[900px] border border-[#E4E5ED] rounded-lg  overflow-x-auto">
            <table className="w-full table-auto border-collapse">
              <thead className="bg-[#E8EEFD]">
                <tr>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">
                    Sr. No.
                  </th>
                  <th className="py-3 px-4 pl-20 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">
                    User
                  </th>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">
                    Email
                  </th>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">
                    Contact
                  </th>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">
                    Role
                  </th>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">
                    Status
                  </th>
                  <th className="py-3 px-4 font-poppins font-bold text-[12px] leading-[18px] text-[#0F1011] text-left">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-[#E4E5ED] font-poppins font-normal text-[13px] leading-[20px] text-[#0F1011]">
                {filteredData.map((user, index) => (
                  <tr
                    key={user.id}
                    className="hover:bg-[#F4F6F9] transition-colors"
                  >
                    <td className="py-4 px-4 font-poppins text-[14px] text-[#0F1011]">
                      {(currentPage - 1) * perPage + index + 1}
                    </td>
                    <td className="py-4 px-4 pl-20">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-semibold text-sm">
                          {user.initials}
                        </div>
                        <span>{user.name}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4">{user.email}</td>
                    <td className="py-4 px-4">{user.contact}</td>
                    <td className="py-4 px-4">
                      <span
                        className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                          user.role === "Healthcare Provider"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-purple-100 text-purple-700"
                        }`}
                      >
                        {user.role}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span
                        className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${
                          user.status === "Active"
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {user.status}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => handleEdit(user.id)}
                          className="p-2 rounded-full hover:bg-[#F4F6F9] transition-colors"
                          title="Edit User"
                        >
                          <PencilIcon
                            size={16}
                            weight="regular"
                            className="text-gray-600"
                          />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(user.id, user.name)}
                          className="p-2 rounded-full hover:bg-red-50 transition-colors"
                          title="Delete User"
                          disabled={deleteUserMutation.isPending}
                        >
                          <TrashIcon
                            size={16}
                            weight="regular"
                            className="text-gray-600 hover:text-red-600"
                          />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}

                {filteredData.length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      className="py-12 text-center text-gray-400 font-poppins"
                    >
                      No users found matching your criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            <div className="flex justify-between items-center mt-6 px-4 pb-4">
              <button
                onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className={`px-4 py-2 rounded-md font-poppins font-medium text-[14px] leading-[20px] transition-colors ${
                  currentPage === 1
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200"
                    : "bg-white text-[#0F1011] border border-[#E4E5ED] hover:bg-[#F4F6F9]"
                }`}
              >
                Previous
              </button>

              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
                Page {currentPage} of {data?.total_pages || 1}
              </span>

              <button
                onClick={() => setCurrentPage((prev) => prev + 1)}
                disabled={currentPage >= (data?.total_pages || 1)}
                className={`px-4 py-2 rounded-md font-poppins font-medium text-[14px] leading-[20px] transition-colors ${
                  currentPage >= (data?.total_pages || 1)
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200"
                    : "bg-white text-[#0F1011] border border-[#E4E5ED] hover:bg-[#F4F6F9]"
                }`}
              >
                Next
              </button>
            </div>
            <AddUserDialog
              isOpen={isUserModalOpen}
              onClose={handleCloseModal}
              userId={selectedUserId}
            />
          </div>
        </div>
      </div>
      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete User"
        message={`Are you sure you want to delete "${userToDeleteName}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmButtonColor="danger"
        isLoading={deleteUserMutation.isPending}
      />
    </>
  );
}
