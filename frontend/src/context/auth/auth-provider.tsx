import SplashScreen from "@/components/loaders/splash-screen";
// import { useAppStore } from '@/store/use-app-store'
import type { AuthenticatedUser } from "@/types/user";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FC, type ReactNode } from "react";
import { AuthContext } from "./auth-context";
import { tokenCookies } from "@/utils/cookies";
import axiosInstance from "@/lib/api";
import { logoutUser } from "@/features/auth/services/authentication-service";

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  // const { setSelectedClinicId } = useAppStore()
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [permissions, setPermissions] = useState<any>(null);
  const [authStatus, setAuthStatus] = useState<
    "loading" | "authenticated" | "offline" | "unauthenticated"
  >("loading");
  // Initialize isAuthenticated from cookies to prevent redirect on reload
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    if (typeof window !== "undefined") {
      return !!tokenCookies.getAccessToken();
    }
    return false;
  });

  // const { isLoading } = useQuery({
  //   queryKey: ['currentUser'],
  //   queryFn: async () => {
  //     const token = localStorage.getItem('token')
  //     if (!token) return null
  //     const { data } = await getDoctorDetails()
  //     setSelectedClinicId(data.clinic_id)
  //     setUser(data)
  //     setIsAuthenticated(true)
  //     return data
  //   },
  //   refetchOnWindowFocus: false,
  //   staleTime: 5 * 60 * 1000 // 5 minutes
  // })

  const { isLoading, refetch: refetchCurrentUser } = useQuery({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const token = tokenCookies.getAccessToken();
      if (!token) {
        setIsAuthenticated(false);
        setAuthStatus("unauthenticated");
        return null;
      }

      try {
        const { data } = await getDoctorDetails();
        setUser(data as AuthenticatedUser);
        setIsAuthenticated(true);
        setAuthStatus("authenticated");
        return data;
      } catch (error) {
        console.error("Failed to fetch user details:", error);

        // 🌐 offline or server down
        if (!navigator.onLine) {
          setAuthStatus("offline");
          // IMPORTANT: do NOT set user
          return null;
        }

        // token invalid etc.
        setIsAuthenticated(false);
        setAuthStatus("unauthenticated");
        return null;
      }
    },
    enabled: !!tokenCookies.getAccessToken(),
    retry: false,
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  const { data: permissionData, isLoading: permissionLoading } = useQuery({
    queryKey: ["permissions"],
    queryFn: enabledPermissions,
    enabled: isAuthenticated && authStatus === "authenticated",
    retry: false,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (!permissionData) {
      return;
    }
    const permissions = Object.keys(permissionData.data).filter(
      (key) => permissionData.data[key] === true,
    );

    setPermissions(permissions);
  }, [permissionData, permissionLoading]);

  const loginMutation = useMutation({
    mutationFn: async (token: string) => {
      tokenCookies.setAccessToken(token);
      // Set authenticated immediately so route guards work
      setIsAuthenticated(true);
      return token;
    },
    onSuccess: async () => {
      // Invalidate and immediately refetch to get fresh user data
      await queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      // Force immediate refetch to ensure fresh data after login
      await refetchCurrentUser();
    },
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      try {
        // Call logout API endpoint to blacklist tokens
        await logoutUser();
      } catch (error) {
        // Even if API call fails, continue with local logout
        console.error("[logoutMutation] Logout API error:", error);
      } finally {
        // Always clear tokens from cookies
        tokenCookies.removeAllTokens();
        localStorage.removeItem("role");
      }
    },
    onSuccess: () => {
      queryClient.setQueryData(["currentUser"], null);
      setUser(null);
      setIsAuthenticated(false);
    },
  });

  const login = (token: string) => loginMutation.mutate(token);
  const logout = () => logoutMutation.mutate();

  const value = {
    user,
    isAuthenticated,
    isLoading,
    authStatus,
    login,
    logout,
    setIsAuthenticated,
    setUser,
    permissions,
  };

  return (
    <AuthContext.Provider value={value}>
      {isLoading ? <SplashScreen /> : children}
    </AuthContext.Provider>
  );
};
// Get logged-in user details using /v1/auth/me API for all roles (doctor, patient, admin)
const getDoctorDetails = async () => {
  const response = await axiosInstance.get("/v1/auth/me");
  return response.data;
};
const enabledPermissions = async () => {
  try {
    const response = await axiosInstance.get("v1/me/permissions");
    return response.data;
  } catch (error) {
    console.error(error);
  }
};
