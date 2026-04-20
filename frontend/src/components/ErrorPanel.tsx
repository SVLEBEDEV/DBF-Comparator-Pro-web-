type ErrorPanelProps = {
  code?: string | null;
  message: string;
};

export function ErrorPanel({ code, message }: ErrorPanelProps) {
  return (
    <div className="panel error-panel">
      <p className="eyebrow">Ошибка</p>
      <h3>{code ?? "comparison_failed"}</h3>
      <p>{message}</p>
    </div>
  );
}
