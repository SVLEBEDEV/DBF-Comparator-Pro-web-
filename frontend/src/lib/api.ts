import { getRuntimeConfig } from "./runtimeConfig";

export type UploadedFileMeta = {
  name: string;
  size_bytes: number;
  encoding: string | null;
  fields: string[];
};

export type UploadResponse = {
  job_id: string;
  status: string;
  files: UploadedFileMeta[];
};

export type RunComparisonPayload = {
  key1: string;
  key2?: string | null;
  structure_only: boolean;
  check_field_order: boolean;
};

export type ComparisonSummary = {
  file1_row_count: number | null;
  file2_row_count: number | null;
  common_field_count: number | null;
  missing_fields_count: number;
  extra_fields_count: number;
  type_mismatches_count: number;
  field_order_mismatches_count: number;
  duplicate_keys_count_file1: number;
  duplicate_keys_count_file2: number;
  missing_rows_count: number;
  extra_rows_count: number;
  data_differences_count: number;
  has_differences: boolean;
};

export type ComparisonCategory = {
  code: string;
  label: string;
  count: number;
  status: "ok" | "attention";
};

export type ComparisonReportInfo = {
  ready: boolean;
  download_url: string | null;
};

export type ComparisonStatusResponse = {
  job_id: string;
  status: string;
  key1: string | null;
  key2: string | null;
  structure_only: boolean;
  check_field_order: boolean;
  warnings: string[];
  error_code: string | null;
  error_message: string | null;
  summary: ComparisonSummary | null;
  categories: ComparisonCategory[];
  report: ComparisonReportInfo;
};

export type PreviewRow = {
  values: Record<string, string | number | boolean | null>;
};

export type ComparisonPreviewResponse = {
  job_id: string;
  section: string;
  limit: number;
  offset: number;
  total: number;
  rows: PreviewRow[];
};

const API_BASE =
  getRuntimeConfig().apiBaseUrl ?? import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function uploadComparisonFiles(file1: File, file2: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file1", file1);
  formData.append("file2", file2);

  const response = await fetch(`${API_BASE}/comparisons/uploads`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "Не удалось загрузить DBF-файлы");
  }

  return (await response.json()) as UploadResponse;
}

export async function runComparison(jobId: string, payload: RunComparisonPayload): Promise<void> {
  const response = await fetch(`${API_BASE}/comparisons/${jobId}/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "Не удалось запустить сравнение");
  }
}

export async function getComparisonStatus(jobId: string): Promise<ComparisonStatusResponse> {
  const response = await fetch(`${API_BASE}/comparisons/${jobId}`);

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "Не удалось получить статус задания");
  }

  return (await response.json()) as ComparisonStatusResponse;
}

export async function getComparisonPreview(
  jobId: string,
  section: string,
  limit = 25,
  offset = 0,
): Promise<ComparisonPreviewResponse> {
  const params = new URLSearchParams({
    section,
    limit: String(limit),
    offset: String(offset),
  });
  const response = await fetch(`${API_BASE}/comparisons/${jobId}/preview?${params.toString()}`);

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "Не удалось получить preview");
  }

  return (await response.json()) as ComparisonPreviewResponse;
}

export async function downloadComparisonReport(jobId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/comparisons/${jobId}/report`);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "Не удалось скачать Excel-отчет");
  }
  return response.blob();
}

export async function deleteComparison(jobId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/comparisons/${jobId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "Не удалось очистить задание");
  }
}
