import type { DashboardRole } from "@/types/dashboard";

interface RoleBadgeProps {
  role: DashboardRole;
}

export function RoleBadge({ role }: RoleBadgeProps) {
  return <span className={`role-badge role-${role}`}>{role}</span>;
}

