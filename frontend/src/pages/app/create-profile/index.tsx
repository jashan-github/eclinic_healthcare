import React, { useState } from "react";
import { useCreateProfile } from "@/features/app/create-profile/hooks/use-create-profile";
import { ArrowLeftIcon, CaretDownIcon } from "@phosphor-icons/react";
import { useNavigate, useRouter } from "@tanstack/react-router";
import { useAuth } from "@/context/auth/auth-context-utils";
import { useLocation } from "@/features/app/my-profile/hooks/use-locations";
import type { CreateProfileData } from "@/features/app/create-profile/services/create-profile-service";

type Profile = {
  title: string;
  firstName: string;
  middleName?: string;
  lastName: string;
  gender?: "male" | "female" | "other";
  date_of_birth?: string;
  country?: string; // display name (optional)
  countryId?: string; // ID for backend
  state?: string;
  stateId?: string;
  city?: string;
  cityId?: string;
  countryCode?: string;
  phone?: string;
  street?: string;
  city_name?: string;
  state_name?: string;
  zip?: string;
};

type Props = {
  initial?: Partial<Profile>;
  onNext?: (profile: Profile) => void;
};

export default function CreateProfile({ initial = {}, onNext }: Props) {
  const { createProfile, isCreating } = useCreateProfile();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const router = useRouter();

  // Parse user name into first/last name parts for prefilling
  const nameParts = (user?.name || "").trim().split(/\s+/);
  const prefillFirstName = user?.first_name || nameParts[0] || "";
  const prefillLastName =
    user?.last_name ||
    (nameParts.length > 1 ? nameParts[nameParts.length - 1] : "");
  const prefillMiddleName =
    user?.middle_name ||
    (nameParts.length > 2 ? nameParts.slice(1, -1).join(" ") : "");

  // Parse phone from user data (API may return combined `phone` like "+910987654321" or separate phone_number)
  const prefillPhone = user?.phone_number || user?.phone || "";
  const prefillGender = user?.gender
    ? (user.gender.toLowerCase() as "male" | "female" | "other")
    : undefined;

  const [selectedCountryId, setSelectedCountryId] = useState<string>("");
  const [selectedStateId, setSelectedStateId] = useState<string>("");
  const [selectedCityId, setSelectedCityId] = useState<string>("");

  const {
    countries,
    states,
    cities,
    isLoadingCountries,
    isLoadingStates,
    isLoadingCities,
  } = useLocation(selectedCountryId, selectedStateId);

  const [form, setForm] = useState<Profile>({
    title: initial.title ?? "Dr",
    firstName: initial.firstName || prefillFirstName,
    middleName: initial.middleName || prefillMiddleName,
    lastName: initial.lastName || prefillLastName,
    gender: (initial.gender as any) ?? prefillGender ?? undefined,
    date_of_birth: initial.date_of_birth ?? "",
    country: initial.country ?? "",
    countryId: initial.countryId ?? "",
    countryCode:
      initial.countryCode || (user?.phone_code ? `+${user.phone_code}` : ""),
    phone: initial.phone || prefillPhone,
    street: initial.street ?? "",
    city: initial.city ?? "",
    state: initial.state ?? "",
    zip: initial.zip ?? "",
  });

  const [touched, setTouched] = useState<Record<string, boolean>>({});

  function update<K extends keyof Profile>(key: K, value: Profile[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function markTouched(key: string) {
    setTouched((prev) => ({ ...prev, [key]: true }));
  }

  function isInvalid(key: keyof Profile) {
    if (!touched[key as string]) return false;
    const val = form[key];
    if (key === "firstName" || key === "lastName")
      return !val || String(val).trim().length === 0;
    return false;
  }

  const isFormValid =
    form.firstName?.trim() &&
    form.lastName?.trim() &&
    form.gender &&
    form.date_of_birth;

  function handleNext(e?: React.FormEvent) {
    e?.preventDefault();

    if (!isFormValid) return;

    // Send data as JSON with title as separate field
    const payload: CreateProfileData = {
      title: form.title.trim(),
      first_name: form.firstName.trim(),
      last_name: form.lastName.trim(),
      city_id: "",
      state_id: "",
      country_id: "",
    };

    if (form.middleName?.trim()) {
      payload.middle_name = form.middleName.trim();
    }

    // Gender capitalized: Male / Female / Other
    if (form.gender) {
      payload.gender =
        form.gender.charAt(0).toUpperCase() + form.gender.slice(1);
    }

    if (form.date_of_birth) payload.date_of_birth = form.date_of_birth;

    if (form.countryId) payload.country_id = form.countryId;
    if (form.stateId) payload.state_id = form.stateId;
    if (form.cityId) payload.city_id = form.cityId;

    if (form.countryCode) payload.phone_code = form.countryCode;
    if (form.phone?.trim()) payload.phone_number = form.phone.trim();
    if (form.street?.trim()) payload.address = form.street.trim();
    if (form.zip?.trim()) payload.postal_code = form.zip.trim();

    createProfile(payload);
    onNext?.(form);
  }

  const handleGoBack = () => {
    logout();
    router.invalidate().then(() => {
      navigate({ to: "/auth/login" });
    });
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-[#F4F6FA] p-6 font-poppins"
      style={{
        border: "1px solid #E2E8F0",
        borderRadius: "16px",
        boxShadow: "6px 7px 20px 0px #0000001A",
      }}
    >
      <form
        onSubmit={handleNext}
        className="w-full max-w-2xl bg-white rounded-2xl shadow-md p-6 sm:p-8 border border-gray-100"
        aria-label="Create Profile"
      >
        {/* Header with back button */}
        <div className="flex items-start gap-3 mb-6">
          <button
            type="button"
            onClick={handleGoBack}
            aria-label="Go back"
            className="p-2 rounded-full bg-[#F2F4F7] flex-shrink-0 hover:bg-gray-200 transition-colors"
          >
            <ArrowLeftIcon size={24} />
          </button>

          <div className="flex flex-col">
            <p className="font-poppins font-normal text-2xl leading-8 text-[#0F1011] m-0">
              Create Profile
            </p>
            <p
              className="m-0 text-gray-500"
              style={{
                fontFamily: "Poppins",
                fontWeight: 400,
                fontStyle: "normal",
                fontSize: "14px",
                lineHeight: "20px",
                letterSpacing: "0%",
                verticalAlign: "middle",
                color: "#0F1011",
              }}
            >
              Help us maintain our medical community's integrity with verified
              credentials.
            </p>
          </div>
        </div>

        {/* Name Section - Same as before */}
        <div className="space-y-1 w-full overflow-hidden">
          <label className="text-sm font-medium text-gray-700 flex items-center gap-1">
            <span className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
              Your name
            </span>
            <span className="text-red-500">*</span>
          </label>

          <div className="flex gap-3 items-center w-full whitespace-nowrap">
            <div className="relative flex-shrink-0">
              <select
                value={form.title}
                onChange={(e) => update("title", e.target.value)}
                className="appearance-none bg-white border border-gray-300 rounded-md px-4 py-2 text-sm font-medium text-gray-900 pr-8 placeholder:font-poppins placeholder:font-normal placeholder:text-sm placeholder:leading-none placeholder:text-[#9CA3AF]"
                style={{ width: "80px" }}
              >
                <option value="Dr">Dr</option>
                <option value="Mr">Mr</option>
                <option value="Mrs">Mrs</option>
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                <CaretDownIcon />
              </div>
            </div>

            <input
              value={form.firstName}
              onChange={(e) => update("firstName", e.target.value)}
              onBlur={() => markTouched("firstName")}
              placeholder="First Name"
              className={`w-full px-3 py-2 border rounded-md text-sm border-gray-200
                ${isInvalid("firstName") ? "border-red-400" : ""}
                placeholder:font-poppins placeholder:font-normal placeholder:text-sm placeholder:leading-none placeholder:text-[#9CA3AF]`}
            />

            <input
              value={form.middleName}
              onChange={(e) => update("middleName", e.target.value)}
              onBlur={() => markTouched("middleName")}
              placeholder="Middle Name"
              className="w-full px-3 py-2 border rounded-md text-sm border-gray-200
                placeholder:font-poppins placeholder:font-normal placeholder:text-sm placeholder:leading-none placeholder:text-[#9CA3AF]"
            />

            <input
              value={form.lastName}
              onChange={(e) => update("lastName", e.target.value)}
              onBlur={() => markTouched("lastName")}
              placeholder="Last Name"
              className={`w-full px-3 py-2 border rounded-md text-sm border-gray-200
                ${isInvalid("lastName") ? "border-red-400" : ""}
                placeholder:font-poppins placeholder:font-normal placeholder:text-sm placeholder:leading-none placeholder:text-[#9CA3AF]`}
            />
          </div>
        </div>

        {/* Gender and DOB */}
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
              Gender <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-3 mt-2">
              <GenderPill
                active={form.gender === "male"}
                onClick={() => update("gender", "male")}
                label="Male"
              />
              <GenderPill
                active={form.gender === "female"}
                onClick={() => update("gender", "female")}
                label="Female"
              />
              <GenderPill
                active={form.gender === "other"}
                onClick={() => update("gender", "other")}
                label="Other"
              />
            </div>
          </div>

          <div>
            <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
              Date of birth <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={form.date_of_birth ?? ""}
              onChange={(e) => update("date_of_birth", e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mt-2
                placeholder:font-poppins placeholder:font-normal placeholder:text-sm placeholder:leading-none placeholder:text-[#9CA3AF]"
            />
          </div>
        </div>

        {/* Country - Same as old, but now cascading */}
        <div className="col-span-12">
          <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
            Country
          </label>
          <select
            value={selectedCountryId}
            onChange={(e) => {
              const id = e.target.value;
              setSelectedCountryId(id);
              update("countryId", id);

              // Reset state & city
              setSelectedStateId("");
              update("stateId", "");
              setSelectedCityId("");
              update("cityId", "");

              // AUTO-FILL PHONE CODE FROM SELECTED COUNTRY
              const selectedCountry = countries.find((c) => c.id === id);
              update(
                "countryCode",
                selectedCountry ? `+${selectedCountry.phonecode}` : "",
              );
            }}
            disabled={isLoadingCountries}
            className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm"
          >
            <option value="">
              {isLoadingCountries ? "Loading countries..." : "Choose Country"}
            </option>
            {countries.map((country) => (
              <option key={country.id} value={country.id}>
                {country.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-12 gap-3 mt-4 items-center">
          {/* Phone Code - Auto-filled & Read-only */}
          <div className="col-span-3 sm:col-span-2">
            <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8] text-nowrap">
              Country Code
            </label>
            <input
              type="text"
              value={form.countryCode}
              readOnly
              placeholder="+Code"
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm bg-gray-50 cursor-not-allowed"
            />
          </div>

          {/* Mobile Number Input */}
          <div className="col-span-9 sm:col-span-10">
            <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
              Mobile Number
            </label>
            <input
              value={form.phone}
              onChange={(e) => update("phone", e.target.value)}
              onBlur={() => markTouched("phone")}
              placeholder="Enter Mobile Number"
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm
        placeholder:font-poppins placeholder:font-normal placeholder:text-sm placeholder:text-[#9CA3AF]"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-4">
          <div>
            <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
              State
            </label>
            <select
              value={selectedStateId}
              onChange={(e) => {
                const id = e.target.value;
                setSelectedStateId(id);
                update("stateId", id);
                setSelectedCityId("");
                update("cityId", "");
              }}
              disabled={!selectedCountryId}
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm"
            >
              <option value="">
                {isLoadingStates ? "Loading..." : "Choose State"}
              </option>
              {states.map((state) => (
                <option key={state.id} value={state.id}>
                  {state.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
              City
            </label>
            <select
              value={selectedCityId}
              onChange={(e) => {
                const id = e.target.value;
                setSelectedCityId(id);
                update("cityId", id);
              }}
              disabled={!selectedStateId}
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm"
            >
              <option value="">
                {isLoadingCities ? "Loading..." : "Select City"}
              </option>
              {cities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mt-4">
          <div>
            <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
              Street Address
            </label>
            <input
              value={form.street}
              onChange={(e) => update("street", e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm placeholder:font-poppins placeholder:font-normal placeholder:text-sm placeholder:leading-none placeholder:text-[#9CA3AF]"
              placeholder="Enter Street Address"
            />
          </div>

          <div>
            <label className="font-poppins font-normal text-xs leading-4 text-[#9EA8B8]">
              Zip Code
            </label>
            <input
              value={form.zip}
              onChange={(e) => update("zip", e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm placeholder:font-poppins placeholder:font-normal placeholder:text-sm placeholder:leading-none placeholder:text-[#9CA3AF]"
              placeholder="Enter Zip Code"
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="mt-6">
          <button
            type="submit"
            disabled={isCreating || !isFormValid}
            className={`w-full py-3 rounded-md text-sm font-semibold text-white transition-all
              ${
                isCreating || !isFormValid
                  ? "bg-gray-400 cursor-not-allowed opacity-60"
                  : "bg-[#002FD4] hover:bg-[#0020B0]"
              }`}
          >
            {isCreating ? "Creating..." : "Next"}
          </button>
        </div>
      </form>
    </div>
  );
}

function GenderPill({
  label,
  active,
  onClick,
}: {
  label: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-3 py-2 text-sm rounded-md border ${active ? "bg-indigo-50 border-indigo-300" : "bg-white border-gray-200"}`}
      aria-pressed={active}
    >
      {label}
    </button>
  );
}
