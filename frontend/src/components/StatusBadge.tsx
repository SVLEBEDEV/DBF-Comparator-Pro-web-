type StatusBadgeProps = {
  tone: "neutral" | "positive" | "danger";
  children: string;
};

export function StatusBadge({ tone, children }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{children}</span>;
}
