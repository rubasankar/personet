export interface Profile {
  id: string;
  name: string;
  email: string;
  bio: string | null;
  location: string | null;
  connection_count: number;
}

export interface ProfileUpdateFieldErrors {
  name?: string;
  bio?: string;
  location?: string;
}

export interface SignupFieldErrors {
  name?: string;
  email?: string;
  password?: string;
}

export interface LoginFieldErrors {
  email?: string;
  password?: string;
}

export interface EducationFieldErrors {
  institution_name?: string;
  institution_type?: string;
  degree?: string;
  department?: string;
  start_year?: string;
  end_year?: string;
}

export interface EducationUpdateFieldErrors {
  degree?: string;
  department?: string;
  end_year?: string;
}

export interface EmploymentFieldErrors {
  company_name?: string;
  role?: string;
  start_year?: string;
  end_year?: string;
}

export interface EmploymentUpdateFieldErrors {
  role?: string;
  end_year?: string;
  is_current?: string;
}

export interface EducationItem {
  institution_name: string;
  institution_type: string;
  degree: string;
  department: string;
  start_year: number;
  end_year: number;
}

export interface EmploymentItem {
  company_name: string;
  role: string;
  start_year: number;
  end_year: number | null;
  is_current: boolean;
}
