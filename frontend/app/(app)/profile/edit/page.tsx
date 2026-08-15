import { EducationForm } from "@/components/profile/EducationForm";
import { EmploymentForm } from "@/components/profile/EmploymentForm";

export default function ProfileEditPage() {
  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto max-w-2xl space-y-8">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Edit Profile
        </h1>
        <EducationForm />
        <EmploymentForm />
      </div>
    </div>
  );
}
