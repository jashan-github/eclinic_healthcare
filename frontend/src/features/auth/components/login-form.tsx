import { useAuthStore } from "@/store/use-auth-store";
import {
  Button,
  Checkbox,
  PasswordInput,
  SegmentedControl,
  Text,
  TextInput,
} from "@mantine/core";
import {
  EnvelopeSimpleIcon,
  UserIcon,
  LockKeyIcon,
} from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useState, type FC, type ReactElement } from "react";
import { toast } from "react-toastify";
import { z } from "zod";

import { PROJECT_NAME } from "@/constants";
import { useAuth } from "@/context/auth/auth-context-utils";
import {
  loginUser,
  type LoginPayload,
} from "../services/authentication-service";
import { tokenCookies } from "@/utils/cookies";
import TabsSegment from "./tab-segment";
import axiosInstance from "@/lib/api";
import { getFirstAllowedRoute } from "@/utils/permission-utils";

const loginSchema = z
  .object({
    loginMethod: z.enum(["email", "username"]),
    emailOrUsername: z.string().min(1, { message: "This field is required" }),
    password: z
      .string()
      .min(8, { message: "Password must be at least 8 characters" }),
    role: z.enum(["Doctor", "Patient", "Staff"]),
    agreedToTerms: z.boolean().refine((val) => val === true, {
      message: "You must agree to the terms",
    }),
  })
  .refine(
    (data) => {
      if (data.loginMethod === "email") {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.emailOrUsername);
      }
      return true;
    },
    {
      message: "Please enter a valid email address",
      path: ["emailOrUsername"],
    },
  );

const LoginForm: FC = (): ReactElement => {
  const { setAuthStep, setFormData } = useAuthStore();

  const [loginMethod, setLoginMethod] = useState<string>("email");
  const { login, setIsAuthenticated } = useAuth();
  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [active, setActive] = useState<string>("Doctor"); // Value 'Doctor' for backend, but displayed as 'Healthcare Provider'

  const handleRoleTabSwitch = (v: string) => {
    setActive(v);
    console.log("Selected tab:", v);
  };

  const loginMutation = useMutation({
    mutationFn: (payload: LoginPayload) => loginUser(payload),

    onSuccess: async ({ data }) => {
      // if (!success) {
      //   toast.error("Login failed");
      //   return;
      // }

      // Store tokens in cookies
      tokenCookies.setAccessToken(data.access_token);
      tokenCookies.setRefreshToken(data.refresh_token);

      // Store role in localStorage (can be moved to cookies if needed)
      localStorage.setItem("role", data.user.role);

      // Call auth context login function to trigger refetch of /v1/auth/me API
      login(data.access_token);

      // Set authenticated immediately so route guards work
      setIsAuthenticated(true);

      setAuthStep(1);

      setFormData({
        loginMethod,
        emailOrUsername,
        password,
        email: emailOrUsername ? emailOrUsername : undefined,
        username: emailOrUsername ? emailOrUsername : undefined,
      });

      toast.success("Login successful!");

      // Wait for user data to be fetched
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Check if there's a redirect parameter in the URL
      const urlParams = new URLSearchParams(window.location.search);
      const redirectParam = urlParams.get("redirect");

      let redirectTo = redirectParam || "/app/dashboard";

      // If no redirect param, determine route based on role and permissions
      if (!redirectParam) {
        try {
          // Fetch permissions to determine the correct redirect
          const permissionsResponse =
            await axiosInstance.get("v1/me/permissions");
          const permissionsData = permissionsResponse.data?.data || {};
          const permissions = Object.keys(permissionsData).filter(
            (key) => permissionsData[key] === true,
          );

          // Get the first allowed route based on role and permissions
          redirectTo = getFirstAllowedRoute(data.user.role, permissions);
        } catch (error) {
          console.error("Failed to fetch permissions for redirect:", error);
          // Fallback to dashboard if permissions fetch fails
          redirectTo = "/app/dashboard";
        }
      }

      // Use window.location for full page reload to ensure context is updated
      window.location.href = redirectTo;
      return;
    },

    onError: (error: any) => {
      const errorsObj = error?.response?.data?.errors ?? {};

      const messages = Object.values(errorsObj).flat();
      const fallback = error?.response?.data?.message || error?.message || "Login failed";
      const formattedMessage = messages.length
        ? messages.map((msg) => `${msg}`).join()
        : fallback;

      if (messages.length > 1) {
        toast.error(
          <div>
            {messages.map((msg: any, index) => (
              <div
                key={index}
                className="flex items-center justify-between gap-1"
              >
                <span>•</span>
                <span className="text-xs font-normal ">{msg}</span>
              </div>
            ))}
          </div>,
        );
      } else {
        toast.error(formattedMessage);
      }
    },
  });

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();

    const result = loginSchema.safeParse({
      loginMethod,
      emailOrUsername,
      password,
      role: active,
      agreedToTerms,
    });
    if (!result.success) {
      result.error.issues.forEach((issue) => toast.error(issue.message));
      return;
    }

    const apiPayload: LoginPayload =
      loginMethod === "email"
        ? { email: emailOrUsername, password, role: active }
        : { username: emailOrUsername, password, role: active };

    loginMutation.mutate(apiPayload);
  };

  const handleTabSwitch = (method: string) => {
    setLoginMethod(method);
    setEmailOrUsername("");
  };

  return (
    <div className="flex flex-col items-center w-full px-4 sm:px-0">
      <div className="flex justify-center items-center flex-col w-full max-w-[620px]">
        <div className="mt-4 mb-8 w-full">
          <TabsSegment value={active} onChange={handleRoleTabSwitch} />
        </div>
      </div>

      <div className="flex justify-center items-center flex-col gap-6 w-full max-w-[492px] rounded-2xl bg-white py-6 px-5 sm:px-6 shadow-[6px_7px_20px_0px_rgba(0,0,0,0.10)] mx-auto">
        <div className="flex justify-center">
          <img
            src="/assets/icons/e-clinic-logo-full.svg"
            alt={PROJECT_NAME}
            className="w-[120px] h-auto sm:w-[150px]"
          />
        </div>

        <form onSubmit={handleLogin}>
          <div className="flex flex-col gap-md w-full">
            {/* Tab Selection */}
            <SegmentedControl
              color="primary"
              radius={"md"}
              size={"sm"}
              value={loginMethod}
              onChange={handleTabSwitch}
              data={[
                {
                  label: (
                    <div className="flex items-center justify-center gap-sm">
                      <EnvelopeSimpleIcon size={18} weight={"bold"} />
                      <span>Email</span>
                    </div>
                  ),
                  value: "email",
                },
                {
                  label: (
                    <div className="flex items-center justify-center gap-sm">
                      <UserIcon size={18} weight={"bold"} />
                      <span>Username</span>
                    </div>
                  ),
                  value: "username",
                },
              ]}
            />

            {/* Email / Username Input */}
            <div>
              <Text
                size="sm"
                fw={400}
                mb={6}
                className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]"
              >
                {loginMethod === "email" ? "Email" : "Username"}
              </Text>
              <TextInput
                autoComplete={loginMethod === "email" ? "email" : "username"}
                onChange={(e) => setEmailOrUsername(e.target.value)}
                placeholder={
                  loginMethod === "email"
                    ? "Enter your email"
                    : "Enter your username"
                }
                size="md"
                leftSection={
                  loginMethod === "email" ? (
                    <EnvelopeSimpleIcon size={18} weight="bold" />
                  ) : (
                    <UserIcon size={18} weight="bold" />
                  )
                }
                leftSectionPointerEvents="none"
                value={emailOrUsername}
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

            {/* Password Input */}
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
                autoComplete="current-password"
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                size="md"
                value={password}
                leftSection={<LockKeyIcon size={18} weight="bold" />}
                leftSectionPointerEvents="none"
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

            {/* Terms Checkbox */}
            <div className="flex items-center gap-xs p-1 ml-0">
              <Checkbox
                checked={agreedToTerms}
                onChange={(e) => setAgreedToTerms(e.currentTarget.checked)}
                size={"14px"}
                styles={{
                  input: {
                    cursor: "pointer",
                    "&:checked": {
                      backgroundColor: "#002FD4",
                      borderColor: "#002FD4",
                    },
                  },
                }}
              />
              <div className="font-normal text-xs">
                By continuing, you agree to our{" "}
                <a
                  className="text-primary"
                  href="/terms-and-conditions"
                  target="_blank"
                >
                  Terms of Use
                </a>
                <span> and </span>
                <a
                  className="text-primary"
                  href="/privacy-policy"
                  target="_blank"
                >
                  Privacy Policy
                </a>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              disabled={loginMutation.isPending || !agreedToTerms}
              loading={loginMutation.isPending}
              size="md"
              type="submit"
              fullWidth
              radius="md"
              className="bg-[#002FD4] h-11 rounded-md px-4 py-2 opacity-100 font-poppins font-semibold text-sm leading-5 tracking-normal text-center align-middle text-[#F8FAFC]"
            >
              Login
            </Button>

            {/* Forgot Password */}
            <div className="flex justify-center">
              <a
                className="text-sm hover:underline hover:text-primary transition-all"
                href="/auth/forgot-password"
              >
                Forgot password?
              </a>
            </div>

            {/* Sign Up Link - Only shown for Patient tab */}
            {active === "Patient" && (
              <div className="flex justify-center">
                <Link
                  to="/auth/signup"
                  className="text-sm hover:underline hover:text-primary transition-all"
                >
                  Don't have an account? Sign up
                </Link>
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginForm;
