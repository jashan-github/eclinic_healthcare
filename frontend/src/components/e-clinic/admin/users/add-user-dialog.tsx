// components/e-clinic/admin/users/add-user-dialog.tsx
import React, { useState, useMemo, useEffect } from "react";
import {
  useCreateUser,
  useUpdateUser,
  useUserById,
} from "@/hooks/use-admin-user-hooks";
import Modal from "@/components/ui/modal";
import FormInput from "@/components/ui/form-input";
import { Select, Loader } from "@mantine/core";
import { countryCodes } from "@/lib/country-codes";
import { useAuth } from "@/context/auth/auth-context-utils";
import type {
  CreateUserPayload,
  UpdateUserPayload,
} from "@/services/admin-user";
import { Eye, EyeSlash, Key } from "@phosphor-icons/react";
import Button from "@/components/ui/button";
import { useAdminDoctors } from "@/hooks/use-admin-doctors";
import { useMedicalServices } from "@/pages/app/settings/hooks/use-medical-services";
import { MultiSelect } from "@mantine/core";
import { toast } from "react-toastify";

const NAME_MIN = 2;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// Backend expects E.164: ^\+?[1-9]\d{1,14}$
const E164_REGEX = /^\+?[1-9]\d{1,14}$/;

interface AddUserDialogProps {
  isOpen: boolean;
  onClose: () => void;
  userId?: string | null; // Optional: if provided, component is in update mode
}

const AddUserDialog: React.FC<AddUserDialogProps> = ({
  isOpen,
  onClose,
  userId,
}) => {
  const isUpdateMode = !!userId;
  const createUserMutation = useCreateUser();
  const updateUserMutation = useUpdateUser();
  const { user } = useAuth();

  // Fetch user data for update mode
  const { data: userData, isLoading: isLoadingUserData } = useUserById(
    userId || null,
  );

  const [countryCode, setCountryCode] = useState<string>("91");
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    phone: "",
    role: "patient" as "doctor" | "patient" | "staff" | "super_admin",
    is_active: true,
    assigned_doctor_id: "",
    // Doctor-specific fields
    education: "",
    years_of_experience: "",
    specializations: [] as string[],
  });

  // Fetch doctors list when role is staff
  const { data: doctors, isLoading: isLoadingDoctors } = useAdminDoctors(
    true,
    isOpen,
  );

  // Fetch medical services for specializations dropdown
  const { data: medicalServices = [] } = useMedicalServices();

  // Prefill form when user data is loaded (update mode)
  useEffect(() => {
    if (userData && isUpdateMode && !isLoadingUserData) {
      // Convert role from API format
      const roleMap: Record<
        string,
        "doctor" | "patient" | "staff" | "super_admin"
      > = {
        Doctor: "doctor",
        doctor: "doctor",
        Patient: "patient",
        patient: "patient",
        Staff: "staff",
        staff: "staff",
        Admin: "super_admin",
        // clinic_admin: "clinic_admin",
        // super_admin: "clinic_admin",
      };

      // Parse phone number to extract country code and phone number
      let phoneNumber = userData.phone || userData.phone_number || "";
      let extractedCountryCode = "91"; // Default to India

      if (phoneNumber && phoneNumber.startsWith("+")) {
        // Try to match country code from the list (try longest codes first)
        const sortedCodes = [...countryCodes].sort(
          (a, b) => b.value.length - a.value.length,
        );
        for (const code of sortedCodes) {
          if (phoneNumber.startsWith(`+${code.value}`)) {
            extractedCountryCode = code.value;
            phoneNumber = phoneNumber.substring(`+${code.value}`.length);
            break;
          }
        }
      }

      setCountryCode(extractedCountryCode);
      setFormData({
        name: userData.name || "",
        email: userData.email || "",
        password: "", // Don't prefill password in update mode
        phone: phoneNumber,
        role:
          roleMap[userData.role?.toLowerCase()] ||
          roleMap[userData.role] ||
          "patient",
        is_active:
          userData.is_active !== undefined
            ? userData.is_active
            : userData.status !== undefined
              ? userData.status
              : true,
        assigned_doctor_id:
          userData.assigned_doctor_id || userData.assigned_doctor?.id || "",
        // Doctor-specific fields
        education: userData.education || "",
        years_of_experience: userData.years_of_experience?.toString() || "",
        specializations: Array.isArray(userData.specializations)
          ? userData.specializations
          : [],
      });
    } else if (!isUpdateMode) {
      // Reset form for create mode
      setCountryCode("91");
      setShowPassword(false);
      setFormData({
        name: "",
        email: "",
        password: "",
        phone: "",
        role: "patient",
        is_active: true,
        assigned_doctor_id: "",
        education: "",
        years_of_experience: "",
        specializations: [],
      });
    }
  }, [userData, isUpdateMode, isLoadingUserData]);

  // Generate strong password function
  const generateStrongPassword = () => {
    const length = 12;
    const lowercase = "abcdefghijklmnopqrstuvwxyz";
    const uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const numbers = "0123456789";
    const symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?";
    const allChars = lowercase + uppercase + numbers + symbols;

    // Ensure at least one character from each category
    let password = "";
    password += lowercase[Math.floor(Math.random() * lowercase.length)];
    password += uppercase[Math.floor(Math.random() * uppercase.length)];
    password += numbers[Math.floor(Math.random() * numbers.length)];
    password += symbols[Math.floor(Math.random() * symbols.length)];

    // Fill the rest randomly
    for (let i = password.length; i < length; i++) {
      password += allChars[Math.floor(Math.random() * allChars.length)];
    }

    // Shuffle the password
    return password
      .split("")
      .sort(() => Math.random() - 0.5)
      .join("");
  };

  const handleGeneratePassword = () => {
    const strongPassword = generateStrongPassword();
    setFormData((prev) => ({
      ...prev,
      password: strongPassword,
    }));
  };

  const countryCodeOptions = useMemo(() => {
    // Filter out duplicates - keep only first occurrence of each country code value
    // (e.g., Kazakhstan and Russia both have +7, so we keep only the first one)
    const seen = new Set<string>();
    return countryCodes
      .filter((code) => {
        if (seen.has(code.value)) {
          return false;
        }
        seen.add(code.value);
        return true;
      })
      .map((code) => ({
        value: code.value,
        label: code.label,
      }));
  }, []);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const updated = {
        ...prev,
        [name]: name === "is_active" ? value === "true" : value,
      };
      // Reset assigned_doctor_id if role changes from staff to something else
      if (name === "role" && value !== "staff") {
        updated.assigned_doctor_id = "";
      }
      // Reset doctor-specific fields if role changes from doctor to something else
      if (name === "role" && value !== "doctor") {
        updated.education = "";
        updated.years_of_experience = "";
        updated.specializations = [];
      }
      return updated;
    });
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value;

    // Remove all non-digit characters
    value = value.replace(/\D/g, "");

    setFormData((prev) => ({
      ...prev,
      phone: value,
    }));
  };

  const isFormValid = isUpdateMode
    ? formData.name.trim() &&
      formData.email.trim() &&
      (formData.role !== "staff" || !!formData.assigned_doctor_id)
    : formData.name.trim() &&
      formData.email.trim() &&
      formData.password.trim().length >= 8 &&
      (formData.role !== "staff" || !!formData.assigned_doctor_id);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const trimmedName = formData.name.trim();
    const trimmedEmail = formData.email.trim();
    const trimmedPhone = formData.phone.trim();

    if (trimmedName.length < NAME_MIN) {
      toast.error(`Name must be at least ${NAME_MIN} characters`);
      return;
    }
    if (!EMAIL_REGEX.test(trimmedEmail)) {
      toast.error("Please enter a valid email address");
      return;
    }
    if (trimmedPhone) {
      const fullPhone = `+${countryCode}${trimmedPhone}`;
      if (!E164_REGEX.test(fullPhone)) {
        toast.error("Please enter a valid phone number");
        return;
      }
    }
    if (formData.role === "doctor") {
      if (!formData.education.trim()) {
        toast.error("Education is required for healthcare providers");
        return;
      }
      if (formData.specializations.length === 0) {
        toast.error("At least one specialization is required for healthcare providers");
        return;
      }
    }

    if (isUpdateMode && userId) {
      // Update mode
      const payload: UpdateUserPayload = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        role: formData.role,
        is_active: formData.is_active,
      };

      // Add phone if provided (optional)
      if (formData.phone.trim()) {
        const fullPhoneNumber = `+${countryCode}${formData.phone.trim()}`;
        payload.phone = fullPhoneNumber;
      }

      // Add assigned_doctor_id if role is staff
      if (formData.role === "staff" && formData.assigned_doctor_id) {
        payload.assigned_doctor_id = formData.assigned_doctor_id;
      }

      // Add doctor-specific fields if role is doctor
      if (formData.role === "doctor") {
        if (formData.education.trim()) {
          payload.education = formData.education.trim();
        }
        if (formData.years_of_experience) {
          payload.years_of_experience = parseInt(formData.years_of_experience);
        }
        if (formData.specializations.length > 0) {
          payload.specializations = formData.specializations;
        }
      }

      updateUserMutation.mutate(
        { userId, payload },
        {
          onSuccess: () => {
            onClose();
          },
        },
      );
    } else {
      // Create mode
      const payload: CreateUserPayload = {
        email: formData.email.trim(),
        password: formData.password.trim(),
        name: formData.name.trim(),
        role: formData.role,
        is_active: formData.is_active,
      };

      // Add phone if provided (optional)
      if (formData.phone.trim()) {
        const fullPhoneNumber = `+${countryCode}${formData.phone.trim()}`;
        payload.phone = fullPhoneNumber;
      }

      // Add clinic_id if available from user context (optional)
      if (user?.clinic_id) {
        payload.clinic_id = user.clinic_id;
      }

      // Add assigned_doctor_id if role is staff
      if (formData.role === "staff" && formData.assigned_doctor_id) {
        payload.assigned_doctor_id = formData.assigned_doctor_id;
      }

      // Add doctor-specific fields if role is doctor
      if (formData.role === "doctor") {
        if (formData.education.trim()) {
          payload.education = formData.education.trim();
        }
        if (formData.years_of_experience) {
          payload.years_of_experience = parseInt(formData.years_of_experience);
        }
        if (formData.specializations.length > 0) {
          payload.specializations = formData.specializations;
        }
      }

      createUserMutation.mutate(payload, {
        onSuccess: () => {
          onClose();
          // Reset form
          setCountryCode("91");
          setShowPassword(false);
          setFormData({
            name: "",
            email: "",
            password: "",
            phone: "",
            role: "patient",
            is_active: true,
            assigned_doctor_id: "",
            education: "",
            years_of_experience: "",
            specializations: [],
          });
        },
      });
    }
  };

  const footer = (
    <>
      <Button
        type="button"
        variant="primary"
        size="md"
        onClick={handleSubmit}
        disabled={
          !isFormValid ||
          (isUpdateMode
            ? updateUserMutation.isPending
            : createUserMutation.isPending)
        }
        className={
          !isFormValid ||
          (isUpdateMode
            ? updateUserMutation.isPending
            : createUserMutation.isPending)
            ? "bg-gray-400 hover:bg-gray-400"
            : ""
        }
      >
        {isUpdateMode
          ? updateUserMutation.isPending
            ? "Updating..."
            : "Update User"
          : createUserMutation.isPending
            ? "Adding..."
            : "Add User"}
      </Button>
      <Button
        type="button"
        variant="secondary"
        size="md"
        onClick={onClose}
        disabled={
          isUpdateMode
            ? updateUserMutation.isPending
            : createUserMutation.isPending
        }
      >
        Cancel
      </Button>
    </>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isUpdateMode ? "Edit User" : "Add New User"}
      footer={footer}
      maxWidth="md"
    >
      {isLoadingUserData && isUpdateMode ? (
        <div className="flex items-center justify-center py-12">
          <Loader />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput
            label="Name"
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />

          <FormInput
            label="Email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
          />

          {!isUpdateMode && (
            <div>
              <label className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] block mb-2">
                Password <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Minimum 8 characters"
                  minLength={8}
                  className="w-full px-4 py-2.5 pr-24 border border-[#E4E5ED] rounded-md focus:outline-none focus:ring-2 focus:ring-[#002FD4] focus:border-[#002FD4] font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]"
                  required
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  <Button
                    type="button"
                    variant="icon"
                    size="md"
                    onClick={handleGeneratePassword}
                    title="Generate Strong Password"
                  >
                    <Key
                      size={16}
                      weight="regular"
                      className="text-[#002FD4]"
                    />
                  </Button>
                  <Button
                    type="button"
                    variant="icon"
                    size="md"
                    onClick={() => setShowPassword(!showPassword)}
                    title={showPassword ? "Hide Password" : "Show Password"}
                  >
                    {showPassword ? (
                      <EyeSlash
                        size={16}
                        weight="regular"
                        className="text-gray-600"
                      />
                    ) : (
                      <Eye
                        size={16}
                        weight="regular"
                        className="text-gray-600"
                      />
                    )}
                  </Button>
                </div>
              </div>
              <p
                className={`text-xs mt-1 ${
                  formData.password.length > 0 && formData.password.length < 8
                    ? "text-red-600 font-medium"
                    : "text-gray-500"
                }`}
              >
                Password must be at least 8 characters long
              </p>
            </div>
          )}

          <div>
            <label className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] block mb-2">
              Phone <span className="text-gray-400 text-xs">(optional)</span>
            </label>
            <div className="flex gap-2">
              <Select
                value={countryCode}
                onChange={(value) => setCountryCode(value || "91")}
                data={countryCodeOptions}
                searchable
                styles={{
                  input: {
                    fontSize: "14px",
                    border: "1px solid #E4E5ED",
                    borderRadius: "8px",
                    fontFamily: "Poppins",
                    minWidth: "140px",
                  },
                }}
                classNames={{
                  input:
                    "font-poppins text-[#0F1011] border-[#E4E5ED] rounded-[8px]",
                  dropdown: "font-poppins",
                }}
              />
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handlePhoneChange}
                placeholder="1234567890"
                className="flex-1 px-4 py-2.5 border border-[#E4E5ED] rounded-md focus:outline-none focus:ring-2 focus:ring-[#002FD4] focus:border-[#002FD4] font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]"
              />
            </div>
          </div>

          <div>
            <label className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] block mb-2">
              Role
            </label>
            <select
              name="role"
              value={formData.role}
              onChange={handleChange}
              className="w-full px-4 py-2.5 border border-[#E4E5ED] rounded-md focus:outline-none focus:ring-2 focus:ring-[#002FD4] focus:border-[#002FD4] font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]"
            >
              <option value="patient">Patient</option>
              <option value="doctor">Healthcare Provider</option>
              <option value="staff">Staff</option>
              <option value="super_admin">Admin</option>
            </select>
          </div>

          {formData.role === "staff" && (
            <div>
              <label className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] block mb-2">
                Assign Doctor <span className="text-red-500">*</span>
              </label>
              {isLoadingDoctors ? (
                <div className="flex items-center gap-2">
                  <Loader size="sm" />
                  <span className="font-poppins font-normal text-[14px] text-[#64748B]">
                    Loading doctors...
                  </span>
                </div>
              ) : (
                <Select
                  value={formData.assigned_doctor_id}
                  onChange={(value) =>
                    setFormData((prev) => ({
                      ...prev,
                      assigned_doctor_id: value || "",
                    }))
                  }
                  data={
                    doctors?.map((doctor) => ({
                      value: doctor.id,
                      label: doctor.name,
                    })) || []
                  }
                  placeholder="Select a doctor"
                  searchable
                  clearable
                  styles={{
                    input: {
                      fontSize: "14px",
                      border: "1px solid #E4E5ED",
                      borderRadius: "8px",
                      fontFamily: "Poppins",
                    },
                  }}
                  classNames={{
                    input:
                      "font-poppins text-[#0F1011] border-[#E4E5ED] rounded-[8px]",
                    dropdown: "font-poppins",
                  }}
                  error={
                    formData.role === "staff" && !formData.assigned_doctor_id
                      ? "Please select a doctor"
                      : undefined
                  }
                />
              )}
            </div>
          )}

          {formData.role === "doctor" && (
            <>
              <FormInput
                label="Education"
                type="text"
                name="education"
                value={formData.education}
                onChange={handleChange}
                placeholder="e.g., MBBS, MD, PhD"
              />

              <FormInput
                label="Years of Experience"
                type="number"
                name="years_of_experience"
                value={formData.years_of_experience}
                onChange={handleChange}
                placeholder="e.g., 5"
                min="0"
              />

              <div>
                <label className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] block mb-2">
                  Specializations
                </label>
                <MultiSelect
                  value={formData.specializations}
                  onChange={(value) =>
                    setFormData((prev) => ({
                      ...prev,
                      specializations: value,
                    }))
                  }
                  data={
                    medicalServices
                      .filter((service) => service.status)
                      .map((service) => ({
                        value: service.id,
                        label: service.name || "N/A",
                      })) || []
                  }
                  placeholder="Select specializations"
                  searchable
                  clearable
                  styles={{
                    input: {
                      fontSize: "14px",
                      border: "1px solid #E4E5ED",
                      borderRadius: "8px",
                      fontFamily: "Poppins",
                    },
                  }}
                  classNames={{
                    input:
                      "font-poppins text-[#0F1011] border-[#E4E5ED] rounded-[8px]",
                    dropdown: "font-poppins",
                  }}
                />
              </div>
            </>
          )}

          <div>
            <label className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] block mb-2">
              Status
            </label>
            <select
              name="is_active"
              value={formData.is_active.toString()}
              onChange={handleChange}
              className="w-full px-4 py-2.5 border border-[#E4E5ED] rounded-md focus:outline-none focus:ring-2 focus:ring-[#002FD4] focus:border-[#002FD4] font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]"
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
        </form>
      )}
    </Modal>
  );
};

export default AddUserDialog;
