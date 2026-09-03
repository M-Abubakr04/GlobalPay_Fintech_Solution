import type { LucideIcon } from "lucide-react";

export function StatCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = "teal"
}: {
  label: string;
  value: string | number;
  detail?: string;
  icon: LucideIcon;
  tone?: "teal" | "blue" | "violet" | "amber" | "red";
}) {
  return (
    <article className={`stat-card stat-${tone}`}>
      <div className="stat-icon"><Icon size={21} /></div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        {detail && <span>{detail}</span>}
      </div>
    </article>
  );
}
