import { useAuth } from "@/context/auth/auth-context-utils";
import LoginForm from "@/features/auth/components/login-form";
import { useEffect, type FC, type ReactElement } from "react";
import { tokenCookies } from "@/utils/cookies";
import { useNavigate } from "@tanstack/react-router";
import { getFirstAllowedRoute } from "@/utils/permission-utils";

const LoginPage: FC = (): ReactElement => {
  const navigate = useNavigate();
  const { setIsAuthenticated, user, permissions } = useAuth();

  useEffect(() => {
    if (!navigator.onLine) return;

    sessionStorage.removeItem("network-redirected");

    const accessToken = tokenCookies.getAccessToken();
    if (!accessToken) return;

    if (!user) {
      return;
    }
    const roleFromStorage = localStorage.getItem("role");
    const userRole = user.role || roleFromStorage || "doctor";

    // Get the first allowed route based on role and permissions
    const redirectTo = getFirstAllowedRoute(userRole, permissions || []);

    setIsAuthenticated(true);

    navigate({
      to: redirectTo,
      replace: true,
    });
  }, [user, permissions, navigate, setIsAuthenticated]);

  return <LoginForm />;
};

export default LoginPage;
