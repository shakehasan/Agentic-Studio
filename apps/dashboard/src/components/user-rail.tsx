import { RoleBadge } from "@/components/role-badge";
import type { DashboardUser } from "@/types/dashboard";

interface UserRailProps {
  users: DashboardUser[];
  selectedUserId: string;
  onSelectUser: (userId: string) => void;
}

export function UserRail({ users, selectedUserId, onSelectUser }: UserRailProps) {
  return (
    <aside className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Users</p>
          <h2>Command Context</h2>
        </div>
      </div>
      <div className="panel-body user-list">
        {users.map((user) => (
          <button
            className={`user-button ${user.id === selectedUserId ? "active" : ""}`}
            key={user.id}
            onClick={() => onSelectUser(user.id)}
            type="button"
          >
            <span className="avatar-row">
              <span className="avatar">{user.avatar_hint}</span>
              <span>
                <strong>{user.name}</strong>
                <br />
                <span className="muted">{user.title}</span>
              </span>
            </span>
            <br />
            <RoleBadge role={user.role} />
          </button>
        ))}
      </div>
    </aside>
  );
}

