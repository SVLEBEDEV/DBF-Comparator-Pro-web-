import type { ChangeEvent } from "react";
import { StatusBadge } from "./StatusBadge";

type FileUploadCardProps = {
  slotLabel: string;
  file: File | null;
  helperText: string;
  resetToken?: number;
  serverMeta?: {
    encoding: string | null;
    fieldsCount: number;
  };
  error?: string | null;
  disabled?: boolean;
  onChange: (file: File | null) => void;
};

export function FileUploadCard({
  slotLabel,
  file,
  helperText,
  resetToken = 0,
  serverMeta,
  error,
  disabled,
  onChange,
}: FileUploadCardProps) {
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    onChange(nextFile);
  };

  return (
    <div className="panel file-card">
      <div className="file-card__header">
        <div>
          <p className="eyebrow">{slotLabel}</p>
          <h3>{file ? file.name : "Файл не выбран"}</h3>
        </div>
        {file ? <StatusBadge tone="neutral">{formatFileSize(file.size)}</StatusBadge> : null}
      </div>

      <label className={`upload-zone ${disabled ? "upload-zone--disabled" : ""}`}>
        <input
          key={`${slotLabel}-${resetToken}-${file?.name ?? "empty"}`}
          accept=".dbf"
          type="file"
          aria-label="Выберите DBF-файл"
          onChange={handleFileChange}
          disabled={disabled}
        />
        <span>Выберите DBF-файл</span>
        <small>{helperText}</small>
      </label>

      {serverMeta ? (
        <div className="file-card__meta">
          <span>Кодировка: {serverMeta.encoding ?? "не определена"}</span>
          <span>Поля: {serverMeta.fieldsCount}</span>
        </div>
      ) : null}

      {error ? <p className="inline-error">{error}</p> : null}
    </div>
  );
}

function formatFileSize(bytes: number) {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${bytes} B`;
}
