type MetricCardProps = {
  eyebrow: string;
  value: string;
  description: string;
};

export function MetricCard({ eyebrow, value, description }: MetricCardProps) {
  return (
    <article className="panel metric-card">
      <p className="eyebrow">{eyebrow}</p>
      <h3>{value}</h3>
      <p>{description}</p>
    </article>
  );
}
