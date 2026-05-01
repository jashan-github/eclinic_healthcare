import { Button, Checkbox, PasswordInput, TextInput } from "@mantine/core";
import { EnvelopeSimpleIcon, LockKeyIcon } from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useState, type FC, type ReactElement } from "react";
import { toast } from "react-toastify";
import { z } from "zod";

import { PROJECT_NAME } from "@/constants";
import { useAuth } from "@/context/auth/auth-context-utils";
import { useAuthStore } from "@/store/use-auth-store";
import {
  loginUser,
  type LoginPayload,
} from "@/features/auth/services/authentication-service";
import { tokenCookies } from "@/utils/cookies";
import axiosInstance from "@/lib/api";
import { getFirstAllowedRoute } from "@/utils/permission-utils";

const adminLoginSchema = z.object({
  email: z
    .string()
    .min(1, { message: "Email is required" })
    .email({ message: "Please enter a valid email address" }),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters long" }),
  agreedToTerms: z.boolean().refine((val) => val === true, {
    message: "You must agree to the Terms of Use and Privacy Policy",
  }),
});

const AdminLoginForm: FC = (): ReactElement => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const { login, setIsAuthenticated } = useAuth();
  const { setAuthStep, setFormData } = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: (payload: LoginPayload) => loginUser(payload),
    onSuccess: async ({ success, data }) => {
      if (!success) {
        toast.error("Login failed");
        return;
      }

      // Store tokens in cookies
      tokenCookies.setAccessToken(data.access_token);
      tokenCookies.setRefreshToken(data.refresh_token);

      // Store role in localStorage
      localStorage.setItem("role", data.user.role);

      // Call auth context login function to trigger refetch of /v1/auth/me API
      login(data.access_token);

      // Set authenticated immediately so route guards work
      setIsAuthenticated(true);

      setAuthStep(1);

      setFormData({
        loginMethod: "email",
        emailOrUsername: email,
        password,
        email: email,
      });

      toast.success("Admin login successful!");

      // Wait for user data to be fetched
      await new Promise((resolve) => setTimeout(resolve, 300));

      let redirectTo = "/app/dashboard";

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
              <div key={index} className="flex items-start gap-1">
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

    const result = adminLoginSchema.safeParse({
      email: email.trim(),
      password,
      agreedToTerms,
    });
    if (!result.success) {
      result.error.issues.forEach((issue) => toast.error(issue.message));
      return;
    }

    const apiPayload: LoginPayload = {
      email: email.trim(),
      password,
      role: "super_admin",
    };

    loginMutation.mutate(apiPayload);
  };

  return (
    <div className="flex flex-col items-center w-full px-4 sm:px-0 mt-5">
      <div className="flex justify-center items-center flex-col gap-8 w-full max-w-[492px] rounded-2xl bg-white py-10 px-6 shadow-[6px_7px_20px_0px_rgba(0,0,0,0.10)] mx-auto">
        {/* Logo */}
        <div className="flex justify-center">
          <img
            src="/assets/icons/e-clinic-logo-full.svg"
            alt={PROJECT_NAME}
            className="w-[150px] h-auto"
          />
        </div>

        <div>
          <div className="font-poppins font-semibold text-2xl leading-8 tracking-[-0.6px] text-center text-[#0F1011]">
            Welcome admin
          </div>
          <div className="font-poppins font-normal text-sm leading-5 text-center text-[#65758B]">
            Login to access your healthcare admin portal
          </div>
        </div>

        <form onSubmit={handleLogin} className="w-full flex flex-col gap-6">
          {/* Email */}
          <div>
            <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011] mb-2 block">
              Email
            </label>
            <TextInput
              leftSection={<EnvelopeSimpleIcon size={18} weight="bold" />}
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              size="md"
              autoComplete="email"
              styles={{
                input: {
                  fontSize: "14px",
                  border: "1px solid #E2E8F0",
                  borderRadius: "8px",
                },
              }}
              classNames={{
                input:
                  "placeholder:font-poppins placeholder:text-[14px] placeholder:text-[#64748B]",
              }}
            />
          </div>

          {/* Password */}
          <div>
            <label className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011] mb-2 block">
              Password
            </label>
            <PasswordInput
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              size="md"
              leftSection={<LockKeyIcon size={18} weight="bold" />}
              leftSectionPointerEvents="none"
              autoComplete="current-password"
              styles={{
                input: {
                  fontSize: "14px",
                  border: "1px solid #E2E8F0",
                  borderRadius: "8px",
                },
              }}
              classNames={{
                input:
                  "placeholder:font-poppins placeholder:text-[14px] placeholder:text-[#64748B]",
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
            type="submit"
            fullWidth
            size="md"
            radius="md"
            loading={loginMutation.isPending}
            disabled={loginMutation.isPending || !agreedToTerms}
            className="bg-[#002FD4] h-11 font-poppins font-semibold text-sm text-[#F8FAFC] hover:bg-[#001fb8]"
          >
            Login
          </Button>
        </form>
      </div>
    </div>
  );
};

export default AdminLoginForm;
