import {
  Button,
  Group,
  PasswordInput,
  Radio,
  Select,
  Text,
  TextInput,
} from "@mantine/core";
import { ArrowLeftIcon } from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, type FC, type ReactElement } from "react";
import { toast } from "react-toastify";
import { z } from "zod";

import { useAuth } from "@/context/auth/auth-context-utils";
// import type { AuthenticatedUser } from "@/types/user";
import { tokenCookies } from "@/utils/cookies";
import { countryCodes } from "@/lib/country-codes";
import {
  signupUser,
  type SignupPayload,
} from "../services/authentication-service";
import { useLocation } from "@/features/app/my-profile/hooks/use-locations";

const signupSchema = z
  .object({
    title: z.enum(["Mr", "Ms", "Mrs", "Dr"], {
      message: "Title is required",
    }),
    firstName: z.string().min(1, { message: "First name is required" }),
    middleName: z.string().optional(),
    lastName: z.string().min(1, { message: "Last name is required" }),
    dob: z.string().min(1, { message: "Date of birth is required" }),
    gender: z.enum(["Male", "Female", "Other"], {
      message: "Gender is required",
    }),
    countryCode: z.string().min(1, { message: "Country code is required" }),
    mobileNumber: z.string().min(1, { message: "Mobile number is required" }),
    email: z.string().email({ message: "Please enter a valid email address" }),
    password: z
      .string()
      .min(8, { message: "Password must be at least 8 characters" }),
    confirmPassword: z
      .string()
      .min(1, { message: "Please confirm your password" }),
    clinicId: z.string().optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

const SignupForm: FC = (): ReactElement => {
  const navigate = useNavigate();
  const { setIsAuthenticated } = useAuth();

  const [title, setTitle] = useState<string>("Mr");
  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState<Date | null>(null);
  const [dobString, setDobString] = useState<string>("");
  const [gender, setGender] = useState<string>("Male");
  const [countryCode, setCountryCode] = useState<string>("91");
  const [mobileNumber, setMobileNumber] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [selectedCountryId, setSelectedCountryId] = useState<string>("");

  const { countries, isLoadingCountries } = useLocation(selectedCountryId, "");

  const selectedCountry = countries.find((c) => c.id === selectedCountryId);
  const autoPhoneCode = selectedCountry?.phonecode.toString() || "91";

  useEffect(() => {
    if (autoPhoneCode) {
      setCountryCode(autoPhoneCode);
    }
  }, [autoPhoneCode]);

  const signupMutation = useMutation({
    mutationFn: (payload: SignupPayload) => signupUser(payload),

    onSuccess: ({ success, data }) => {
      if (!success) {
        toast.error("Signup failed");
        return;
      }

      // Store token in cookies (assuming signup also returns refresh_token)
      tokenCookies.setAccessToken(data.token);
      // If signup response includes refresh_token, store it too
      if (data.refresh_token) {
        tokenCookies.setRefreshToken(data.refresh_token);
      }
      localStorage.setItem("role", data.user.role);
      setIsAuthenticated(true);

      // const userForStore: AuthenticatedUser = {
      //   ...data.user,
      //   name: data.user.email.split('@')[0],
      //   short_description: '',
      //   experience: '',
      //   education: '',
      //   gender: gender,
      //   profile_img: '',
      //   isWritingPad: null,
      //   total_credits: 0,
      //   availableCredits: 0,
      //   available_credits: false,
      //   role: data.user.role
      // }
      // setUser(userForStore);

      toast.success("Account created successfully!");
      navigate({ to: "/app/dashboard" });
      // navigate({ to: '/app/patient-profile' })
    },

    onError: (error) => {
      console.log(error);
      toast.error("Something went wrong. Please try again.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const payload = {
      title,
      firstName,
      middleName,
      lastName,
      dob: dobString || (dob ? dob.toISOString().split("T")[0] : ""),
      gender,
      countryCode,
      mobileNumber,
      email,
      password,
      confirmPassword,
    };

    const result = signupSchema.safeParse(payload);
    if (!result.success) {
      result.error.issues.forEach((issue) => toast.error(issue.message));
      return;
    }

    const apiPayload: SignupPayload = {
      title,
      first_name: firstName,
      middle_name: middleName || undefined,
      last_name: lastName,
      date_of_birth: dobString || (dob ? dob.toISOString().split("T")[0] : ""),
      gender: gender as "Male" | "Female" | "Other",
      phone_code: countryCode,
      phone_number: mobileNumber,
      email,
      password,
      password_confirmation: confirmPassword,
      role: "patient",
      country_id: selectedCountryId,
    };

    signupMutation.mutate(apiPayload);
  };

  // Filter duplicates by value, keeping the first occurrence
  const seenValues = new Set<string>();
  const countryCodeOptions = countryCodes
    .filter((code) => {
      if (seenValues.has(code.value)) {
        return false;
      }
      seenValues.add(code.value);
      return true;
    })
    .map((code) => ({
      value: code.value,
      label: code.label,
    }));

  return (
    <div className="flex flex-col items-center w-full px-4 sm:px-0">
      <div className="flex justify-center items-center flex-col w-full max-w-[800px]">
        <div className="w-full max-w-[600px] rounded-2xl bg-white py-6 px-5 sm:px-6 shadow-[6px_7px_20px_0px_rgba(0,0,0,0.10)] mx-auto">
          {/* Back Button and Title */}
          <div className="flex items-center gap-4 mb-4">
            <Link
              to="/auth/login"
              className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition-colors"
            >
              <ArrowLeftIcon size={20} weight="bold" />
            </Link>
            <div className="flex flex-col">
              <Text
                size="xl"
                fw={600}
                className="font-poppins font-bold text-[24px] leading-[32px] text-[#0F1011]"
              >
                Create Profile
              </Text>
              <Text
                size="sm"
                className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mt-1"
              >
                Help us maintain our medical community's integrity with verified
                credentials.
              </Text>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-md w-full">
              {/* Your Name */}
              <div>
                <Text
                  size="sm"
                  fw={400}
                  mb={6}
                  className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]"
                >
                  Your name<span className="text-red-500">*</span>
                </Text>
                <Group gap="sm" grow>
                  <Select
                    value={title}
                    onChange={(value) => setTitle(value || "Mr")}
                    data={["Mr", "Ms", "Mrs", "Dr"]}
                    styles={{
                      input: {
                        fontSize: "14px",
                        border: "1px solid #E2E8F0",
                        borderRadius: "8px",
                        fontFamily: "Poppins",
                      },
                    }}
                    classNames={{
                      input:
                        "font-poppins text-[#BA1A1A] border-[#E2E8F0] rounded-[8px]",
                    }}
                  />
                  <TextInput
                    placeholder="First Name"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    styles={{
                      input: {
                        fontSize: "14px",
                        border: "1px solid #E2E8F0",
                        borderRadius: "8px",
                        opacity: 1,
                      },
                    }}
                    classNames={{
                      input:
                        "font-poppins text-[#BA1A1A] border-[#E2E8F0] rounded-[8px] placeholder:font-poppins placeholder:text-[14px] placeholder:leading-[100%] placeholder:font-normal placeholder:text-[#64748B]",
                    }}
                  />
                  <TextInput
                    placeholder="Middle Name"
                    value={middleName}
                    onChange={(e) => setMiddleName(e.target.value)}
                    styles={{
                      input: {
                        fontSize: "14px",
                        border: "1px solid #E2E8F0",
                        borderRadius: "8px",
                        opacity: 1,
                      },
                    }}
                    classNames={{
                      input:
                        "font-poppins text-[#BA1A1A] border-[#E2E8F0] rounded-[8px] placeholder:font-poppins placeholder:text-[14px] placeholder:leading-[100%] placeholder:font-normal placeholder:text-[#64748B]",
                    }}
                  />
                  <TextInput
                    placeholder="Last Name"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    styles={{
                      input: {
                        fontSize: "14px",
                        border: "1px solid #E2E8F0",
                        borderRadius: "8px",
                        opacity: 1,
                      },
                    }}
                    classNames={{
                      input:
                        "font-poppins text-[#BA1A1A] border-[#E2E8F0] rounded-[8px] placeholder:font-poppins placeholder:text-[14px] placeholder:leading-[100%] placeholder:font-normal placeholder:text-[#64748B]",
                    }}
                  />
                </Group>
              </div>

              {/* Date of Birth */}
              <div>
                <Text
                  size="sm"
                  fw={400}
                  mb={6}
                  className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]"
                >
                  Date of birth<span className="text-red-500">*</span>
                </Text>
                <input
                  type="date"
                  value={dobString}
                  onChange={(e) => {
                    const value = e.target.value;
                    setDobString(value);
                    if (value) {
                      setDob(new Date(value));
                    } else {
                      setDob(null);
                    }
                  }}
                  className="w-full px-4 py-2 text-[14px] font-poppins border border-[#E2E8F0] rounded-[8px] focus:outline-none focus:border-[#002FD4]"
                  required
                />
              </div>

              {/* Gender */}
              <div>
                <Text
                  size="sm"
                  fw={400}
                  mb={6}
                  className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]"
                >
                  Gender<span className="text-red-500">*</span>
                </Text>
                <Group gap="md">
                  <Radio.Group value={gender} onChange={setGender}>
                    <Group gap="md">
                      <Radio
                        value="Male"
                        label="Male"
                        styles={{
                          label: {
                            fontFamily: "Poppins",
                            fontSize: "14px",
                          },
                        }}
                      />
                      <Radio
                        value="Female"
                        label="Female"
                        styles={{
                          label: {
                            fontFamily: "Poppins",
                            fontSize: "14px",
                          },
                        }}
                      />
                      <Radio
                        value="Other"
                        label="Other"
                        styles={{
                          label: {
                            fontFamily: "Poppins",
                            fontSize: "14px",
                          },
                        }}
                      />
                    </Group>
                  </Radio.Group>
                </Group>
              </div>

              {/* Mobile Number With Country Code */}
              {/* Mobile Number With Country Code + Country Selector */}
              <div>
                <Text
                  size="sm"
                  fw={400}
                  mb={6}
                  className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]"
                >
                  Country & Mobile Number<span className="text-red-500">*</span>
                </Text>

                {/* Country Selector */}
                <Select
                  placeholder={
                    isLoadingCountries
                      ? "Loading countries..."
                      : "Select your country"
                  }
                  data={countries.map((country) => ({
                    value: country.id,
                    label: country.name,
                  }))}
                  value={selectedCountryId}
                  onChange={(value) => setSelectedCountryId(value || "")}
                  searchable
                  styles={{
                    input: {
                      fontSize: "14px",
                      border: "1px solid #E2E8F0",
                      borderRadius: "8px",
                      fontFamily: "Poppins",
                    },
                  }}
                  classNames={{
                    input:
                      "font-poppins text-[#0F1011] border-[#E2E8F0] rounded-[8px]",
                  }}
                  mb="sm"
                />

                {/* Phone Code + Mobile Number */}
                <Group gap="sm" grow>
                  <Select
                    value={countryCode}
                    onChange={(value) => setCountryCode(value || "91")}
                    data={countryCodeOptions}
                    disabled // optional: disable manual edit since it's auto-filled
                    styles={{
                      input: {
                        fontSize: "14px",
                        border: "1px solid #E2E8F0",
                        borderRadius: "8px",
                        fontFamily: "Poppins",
                      },
                    }}
                  />
                  <TextInput
                    placeholder="Enter Mobile Number"
                    value={mobileNumber}
                    onChange={(e) => setMobileNumber(e.target.value)}
                    styles={{
                      input: {
                        fontSize: "14px",
                        border: "1px solid #E2E8F0",
                        borderRadius: "8px",
                      },
                    }}
                    classNames={{
                      input:
                        "placeholder:font-poppins placeholder:text-[14px] placeholder:font-normal placeholder:text-[#64748B]",
                    }}
                  />
                </Group>
              </div>

              {/* Email */}
              <div>
                <Text
                  size="sm"
                  fw={400}
                  mb={6}
                  className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]"
                >
                  Email
                </Text>
                <TextInput
                  type="email"
                  placeholder="Enter Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  styles={{
                    input: {
                      fontSize: "14px",
                      border: "1px solid #E2E8F0",
                      borderRadius: "8px",
                      opacity: 1,
                    },
                  }}
                  classNames={{
                    input:
                      "font-poppins text-[#BA1A1A] border-[#E2E8F0] rounded-[8px] placeholder:font-poppins placeholder:text-[14px] placeholder:leading-[100%] placeholder:font-normal placeholder:text-[#64748B]",
                  }}
                />
              </div>

              {/* Password */}
              <div>
                <Text
                  size="sm"
                  fw={400}
                  mb={6}
                  className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]"
                >
                  Password
                </Text>
                <PasswordInput
                  placeholder="Enter Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  styles={{
                    input: {
                      fontSize: "14px",
                      fontFamily: "Poppins",
                      color: "#1A1A1A",
                      border: "1px solid #E2E8F0",
                      borderRadius: "8px",
                      opacity: 1,
                    },
                  }}
                  classNames={{
                    input:
                      "placeholder:font-poppins placeholder:text-[14px] placeholder:leading-[100%] placeholder:font-normal placeholder:text-[#64748B]",
                  }}
                />
              </div>

              {/* Confirm Password */}
              <div>
                <Text
                  size="sm"
                  fw={400}
                  mb={6}
                  className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]"
                >
                  Confirm password
                </Text>
                <PasswordInput
                  placeholder="Enter Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  styles={{
                    input: {
                      fontSize: "14px",
                      fontFamily: "Poppins",
                      color: "#1A1A1A",
                      border: "1px solid #E2E8F0",
                      borderRadius: "8px",
                      opacity: 1,
                    },
                  }}
                  classNames={{
                    input:
                      "placeholder:font-poppins placeholder:text-[14px] placeholder:leading-[100%] placeholder:font-normal placeholder:text-[#64748B]",
                  }}
                />
              </div>

              {/* Submit Button */}
              <Button
                disabled={signupMutation.isPending}
                loading={signupMutation.isPending}
                size="md"
                type="submit"
                fullWidth
                radius="md"
                className="bg-[#E2E8F0] h-11 rounded-md px-4 py-2 opacity-100 font-poppins font-semibold text-sm leading-5 tracking-normal text-center align-middle text-[#0F1011] hover:bg-[#CBD5E1]"
              >
                Create Account
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SignupForm;
