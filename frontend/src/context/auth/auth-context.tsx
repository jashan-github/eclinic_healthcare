import type { AuthenticatedUser } from "@/types/user";
import { createContext } from "react";

export type AuthContextType = {
  isAdmin?: boolean;
  isAuthenticated: boolean;
  isDoctor?: boolean;
  isLoading?: boolean;
  isPatient?: boolean;
  isStaff?: boolean;
  login: (token: string) => void;
  logout: () => void;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  setUser: (user: AuthenticatedUser) => void;
  user: AuthenticatedUser | null;
  refetchUser?: () => void;
  permissions?: string[];
};

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);
