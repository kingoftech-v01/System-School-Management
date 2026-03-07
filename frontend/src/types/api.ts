export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  middle_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  role_display: string;
  is_student: boolean;
  is_lecturer: boolean;
  is_parent: boolean;
  is_dep_head: boolean;
  is_staff: boolean;
  is_active: boolean;
  phone: string;
  street_address: string;
  city: string;
  province: string;
  postal_code: string;
  country: string;
  picture: string | null;
  date_joined: string;
  last_login: string | null;
}

export type UserRole =
  | 'student'
  | 'professor'
  | 'parent'
  | 'direction'
  | 'accountant'
  | 'secretary'
  | 'librarian'
  | 'registrar'
  | 'prefet'
  | 'admin';

export interface AuthTokens {
  access: string;
  refresh: string;
  user: User;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface ApiError {
  detail?: string;
  non_field_errors?: string[];
  [key: string]: unknown;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface NavItem {
  name: string;
  path: string;
  icon: string;
}

export interface NavigationResponse {
  role: string;
  navigation: NavItem[];
}

export interface PermissionsResponse {
  role: string;
  permissions: Record<string, boolean>;
}
