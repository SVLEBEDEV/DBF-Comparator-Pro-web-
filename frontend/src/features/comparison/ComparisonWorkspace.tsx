import { useEffect, useMemo, useRef, useState } from "react";

import { ErrorPanel } from "../../components/ErrorPanel";
import { FileUploadCard } from "../../components/FileUploadCard";
import { SelectField } from "../../components/SelectField";
import { StatusBadge } from "../../components/StatusBadge";
import {
  deleteComparison,
  downloadComparisonReport,
  getComparisonPreview,
  getComparisonStatus,
  runComparison,
  uploadComparisonFiles,
  type ComparisonPreviewResponse,
  type ComparisonStatusResponse,
  type UploadResponse,
} from "../../lib/api";

type UploadState = {
  file1: File | null;
  file2: File | null;
};

const initialUploadState: UploadState = {
  file1: null,
  file2: null,
};

type CategoryRow = {
  id: string;
  label: string;
  value: string;
  tone: "neutral" | "positive" | "danger";
  skipped?: boolean;
  previewSection?: string;
  previewFilter?: (row: Record<string, string | number | boolean | null>) => boolean;
  syntheticRows?: Array<Record<string, string | number | boolean | null>>;
};

const DEFAULT_CATEGORY = "data_differences";

export function ComparisonWorkspace() {
  const [files, setFiles] = useState<UploadState>(initialUploadState);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [key1, setKey1] = useState("");
  const [key2, setKey2] = useState("");
  const [structureOnly, setStructureOnly] = useState(false);
  const [checkFieldOrder, setCheckFieldOrder] = useState(false);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonStatus, setComparisonStatus] = useState<ComparisonStatusResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState(DEFAULT_CATEGORY);
  const [preview, setPreview] = useState<ComparisonPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewOffset, setPreviewOffset] = useState(0);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [resetToken, setResetToken] = useState(0);
  const [lastRunSignature, setLastRunSignature] = useState<string | null>(null);
  const currentJobIdRef = useRef<string | null>(null);
  const file1PanelRef = useRef<HTMLDivElement | null>(null);
  const file2PanelRef = useRef<HTMLDivElement | null>(null);
  const actionPanelRef = useRef<HTMLDivElement | null>(null);
  const controlsPanelRef = useRef<HTMLDivElement | null>(null);
  const summaryPanelRef = useRef<HTMLDivElement | null>(null);
  const [matchedHeights, setMatchedHeights] = useState<{ top: number | null; bottom: number | null }>({
    top: null,
    bottom: null,
  });

  const availableFields = useMemo(() => {
    if (!uploadResult?.files.length) {
      return [];
    }

    const [first, second] = uploadResult.files;
    const secondFields = new Set(second?.fields ?? []);
    return first.fields.filter((field) => secondFields.has(field));
  }, [uploadResult]);

  const canRun = Boolean(uploadResult && key1 && !loading && !running);
  const canDownload = Boolean(uploadResult?.job_id && comparisonStatus?.report.ready && !downloadLoading);
  const currentParamsSignature = useMemo(
    () => JSON.stringify({ key1, key2, structureOnly, checkFieldOrder }),
    [key1, key2, structureOnly, checkFieldOrder],
  );
  const filesSignature = useMemo(() => {
    if (!files.file1 || !files.file2) {
      return null;
    }
    return [
      files.file1.name,
      files.file1.size,
      files.file1.lastModified,
      files.file2.name,
      files.file2.size,
      files.file2.lastModified,
    ].join(":");
  }, [files]);
  const [lastUploadedSignature, setLastUploadedSignature] = useState<string | null>(null);

  const categoryRows = useMemo<CategoryRow[]>(() => {
    const summary = comparisonStatus?.summary;
    const [file1Meta, file2Meta] = uploadResult?.files ?? [];
    const file1Encoding = file1Meta?.encoding ?? "не определена";
    const file2Encoding = file2Meta?.encoding ?? "не определена";
    const encodings = uploadResult ? `${file1Encoding} / ${file2Encoding}` : "—";
    const file1Rows = summary?.file1_row_count ?? 0;
    const file2Rows = summary?.file2_row_count ?? 0;
    const rowCounts = summary ? `${file1Rows} / ${file2Rows}` : "—";
    const duplicateCount =
      summary ? summary.duplicate_keys_count_file1 + summary.duplicate_keys_count_file2 : 0;
    const uniqueKeysLabel =
      summary === undefined || summary === null
        ? "—"
        : duplicateCount === 0
          ? "Ключи уникальны"
          : "Есть неуникальные ключи";
    const skippedValue = "—";
    const isStructureOnly = comparisonStatus?.structure_only ?? false;
    const rowsMatch = summary ? file1Rows === file2Rows : null;
    const encodingsMatch = uploadResult ? file1Encoding === file2Encoding : null;

    return [
      {
        id: "row_count",
        label: "Строк",
        value: rowCounts,
        tone: rowsMatch === null ? "neutral" : rowsMatch ? "positive" : "danger",
        syntheticRows: summary
          ? [
              { файл: file1Meta?.name ?? "Файл 1", строк: file1Rows, статус: rowsMatch ? "совпадает" : "расхождение" },
              { файл: file2Meta?.name ?? "Файл 2", строк: file2Rows, статус: rowsMatch ? "совпадает" : "расхождение" },
            ]
          : [],
      },
      {
        id: "encoding",
        label: "Кодировка",
        value: encodings,
        tone: encodingsMatch === null ? "neutral" : encodingsMatch ? "positive" : "danger",
      },
      {
        id: "unique_keys",
        label: "Уникальность ключей",
        value: isStructureOnly ? skippedValue : uniqueKeysLabel,
        tone: isStructureOnly ? ("neutral" as const) : summary && duplicateCount > 0 ? ("danger" as const) : ("positive" as const),
        skipped: isStructureOnly,
        previewSection: isStructureOnly ? undefined : "DUPLICATES",
      },
      {
        id: "duplicate_keys",
        label: "Дубликаты ключей",
        value: isStructureOnly ? skippedValue : String(duplicateCount),
        tone: isStructureOnly ? ("neutral" as const) : duplicateCount > 0 ? ("danger" as const) : ("positive" as const),
        skipped: isStructureOnly,
        previewSection: isStructureOnly ? undefined : "DUPLICATES",
      },
      {
        id: "field_order",
        label: "Очередность полей",
        value: String(summary?.field_order_mismatches_count ?? 0),
        tone: (summary?.field_order_mismatches_count ?? 0) > 0 ? ("danger" as const) : ("positive" as const),
        previewSection: "FIELD_ORDER",
      },
      {
        id: "missing_fields",
        label: "Отсутствующие поля",
        value: String(summary?.missing_fields_count ?? 0),
        tone: (summary?.missing_fields_count ?? 0) > 0 ? ("danger" as const) : ("positive" as const),
        previewSection: "STRUCTURE",
        previewFilter: (row) => row.issue === "missing_in_file2",
      },
      {
        id: "extra_fields",
        label: "Лишние поля",
        value: String(summary?.extra_fields_count ?? 0),
        tone: (summary?.extra_fields_count ?? 0) > 0 ? ("danger" as const) : ("positive" as const),
        previewSection: "STRUCTURE",
        previewFilter: (row) => row.issue === "extra_in_file2",
      },
      {
        id: "missing_rows",
        label: "Отсутствующие строки",
        value: isStructureOnly ? skippedValue : String(summary?.missing_rows_count ?? 0),
        tone: isStructureOnly ? ("neutral" as const) : (summary?.missing_rows_count ?? 0) > 0 ? ("danger" as const) : ("positive" as const),
        skipped: isStructureOnly,
        previewSection: isStructureOnly ? undefined : "RECONCILIATION",
        previewFilter: isStructureOnly ? undefined : (row) => row.issue === "missing_in_file2",
      },
      {
        id: "extra_rows",
        label: "Лишние строки",
        value: isStructureOnly ? skippedValue : String(summary?.extra_rows_count ?? 0),
        tone: isStructureOnly ? ("neutral" as const) : (summary?.extra_rows_count ?? 0) > 0 ? ("danger" as const) : ("positive" as const),
        skipped: isStructureOnly,
        previewSection: isStructureOnly ? undefined : "RECONCILIATION",
        previewFilter: isStructureOnly ? undefined : (row) => row.issue === "extra_in_file2",
      },
      {
        id: "type_mismatches",
        label: "Несоответствие типов",
        value: String(summary?.type_mismatches_count ?? 0),
        tone: (summary?.type_mismatches_count ?? 0) > 0 ? ("danger" as const) : ("positive" as const),
        previewSection: "TYPES",
      },
      {
        id: "data_differences",
        label: "Различия в данных",
        value: isStructureOnly ? skippedValue : String(summary?.data_differences_count ?? 0),
        tone: isStructureOnly ? ("neutral" as const) : (summary?.data_differences_count ?? 0) > 0 ? ("danger" as const) : ("positive" as const),
        skipped: isStructureOnly,
        previewSection: isStructureOnly ? undefined : "DETAILS",
      },
    ];
  }, [comparisonStatus, uploadResult]);

  const selectedCategoryRow = useMemo(
    () => categoryRows.find((row) => row.id === selectedCategory) ?? categoryRows[0] ?? null,
    [categoryRows, selectedCategory],
  );

  useEffect(() => {
    if (!categoryRows.length) {
      return;
    }
    const hasSelected = categoryRows.some((row) => row.id === selectedCategory);
    if (!hasSelected) {
      setSelectedCategory(categoryRows[0]?.id ?? DEFAULT_CATEGORY);
      setPreviewOffset(0);
    }
  }, [categoryRows, selectedCategory]);

  useEffect(() => {
    if (!filesSignature || filesSignature === lastUploadedSignature || !files.file1 || !files.file2) {
      return;
    }

    const file1 = files.file1;
    const file2 = files.file2;
    let cancelled = false;

    const syncStructure = async () => {
      setLoading(true);
      setError(null);
      setPreviewError(null);
      setUploadResult(null);
      setComparisonStatus(null);
      setPreview(null);
      setPreviewOffset(0);
      setSelectedCategory(DEFAULT_CATEGORY);

      const previousJobId = currentJobIdRef.current;
      if (previousJobId) {
        try {
          await deleteComparison(previousJobId);
        } catch {
          // Ignore best-effort cleanup when user is replacing files.
        }
        currentJobIdRef.current = null;
      }

      try {
        const result = await uploadComparisonFiles(file1, file2);
        if (cancelled) {
          return;
        }

        currentJobIdRef.current = result.job_id;
        setUploadResult(result);
        setLastUploadedSignature(filesSignature);
        setLastRunSignature(null);

        const [first, second] = result.files;
        const commonFields = first.fields.filter((field) => new Set(second.fields).has(field));
        const preferredKey = commonFields.find((field) => field.toUpperCase() === "KEY1") ?? commonFields[0] ?? "";
        setKey1(preferredKey);
        setKey2("");
      } catch (uploadError) {
        if (cancelled) {
          return;
        }
        setLastUploadedSignature(null);
        setUploadResult(null);
        setError(uploadError instanceof Error ? uploadError.message : "Ошибка загрузки файлов");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void syncStructure();

    return () => {
      cancelled = true;
    };
  }, [files, filesSignature, lastUploadedSignature]);

  useEffect(() => {
    if (!comparisonStatus || !lastRunSignature) {
      return;
    }
    if (currentParamsSignature === lastRunSignature) {
      return;
    }

    setComparisonStatus(null);
    setPreview(null);
    setPreviewOffset(0);
  }, [comparisonStatus, currentParamsSignature, lastRunSignature]);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return undefined;
    }

    const media = window.matchMedia("(max-width: 1080px)");
    const syncHeights = () => {
      if (media.matches) {
        setMatchedHeights({ top: null, bottom: null });
        return;
      }
      const topHeight = Math.max(
        file1PanelRef.current?.scrollHeight ?? 0,
        file2PanelRef.current?.scrollHeight ?? 0,
        actionPanelRef.current?.scrollHeight ?? 0,
      );
      const bottomHeight = Math.max(
        controlsPanelRef.current?.scrollHeight ?? 0,
        summaryPanelRef.current?.scrollHeight ?? 0,
      );
      setMatchedHeights({
        top: topHeight || null,
        bottom: bottomHeight || null,
      });
    };

    syncHeights();

    if (typeof ResizeObserver === "undefined") {
      media.addEventListener("change", syncHeights);
      window.addEventListener("resize", syncHeights);
      return () => {
        media.removeEventListener("change", syncHeights);
        window.removeEventListener("resize", syncHeights);
      };
    }

    const observer = new ResizeObserver(() => {
      syncHeights();
    });

    if (file1PanelRef.current) {
      observer.observe(file1PanelRef.current);
    }
    if (file2PanelRef.current) {
      observer.observe(file2PanelRef.current);
    }
    if (actionPanelRef.current) {
      observer.observe(actionPanelRef.current);
    }
    if (controlsPanelRef.current) {
      observer.observe(controlsPanelRef.current);
    }
    if (summaryPanelRef.current) {
      observer.observe(summaryPanelRef.current);
    }

    media.addEventListener("change", syncHeights);
    window.addEventListener("resize", syncHeights);

    return () => {
      observer.disconnect();
      media.removeEventListener("change", syncHeights);
      window.removeEventListener("resize", syncHeights);
    };
  }, [uploadResult, comparisonStatus, key1, key2, structureOnly, checkFieldOrder, loading]);

  useEffect(() => {
    if (!uploadResult?.job_id) {
      return undefined;
    }
    if (!comparisonStatus || !["queued", "processing"].includes(comparisonStatus.status)) {
      return undefined;
    }

    const timer = window.setInterval(async () => {
      try {
        const nextStatus = await getComparisonStatus(uploadResult.job_id);
        setComparisonStatus(nextStatus);
        if (!["queued", "processing"].includes(nextStatus.status)) {
          setRunning(false);
        }
      } catch (pollError) {
        setRunning(false);
        setError(pollError instanceof Error ? pollError.message : "Ошибка обновления статуса");
      }
    }, 2000);

    return () => window.clearInterval(timer);
  }, [comparisonStatus, uploadResult]);

  useEffect(() => {
    if (!uploadResult?.job_id || comparisonStatus?.status !== "completed" || !selectedCategoryRow?.previewSection) {
      return;
    }

    const previewSection = selectedCategoryRow.previewSection;
    const loadPreview = async () => {
      setPreviewLoading(true);
      setPreviewError(null);
      try {
        const nextPreview = await getComparisonPreview(uploadResult.job_id, previewSection, 25, previewOffset);
        setPreview(nextPreview);
      } catch (loadError) {
        setPreview(null);
        setPreviewError(loadError instanceof Error ? loadError.message : "Ошибка загрузки preview");
      } finally {
        setPreviewLoading(false);
      }
    };

    void loadPreview();
  }, [comparisonStatus?.status, previewOffset, selectedCategoryRow, uploadResult]);

  const handleReset = () => {
    const previousJobId = currentJobIdRef.current;
    setFiles(initialUploadState);
    currentJobIdRef.current = null;
    setUploadResult(null);
    setLastUploadedSignature(null);
    setKey1("");
    setKey2("");
    setStructureOnly(false);
    setCheckFieldOrder(false);
    setComparisonStatus(null);
    setPreview(null);
    setPreviewOffset(0);
    setSelectedCategory(DEFAULT_CATEGORY);
    setLastRunSignature(null);
    setRunning(false);
    setLoading(false);
    setError(null);
    setPreviewError(null);
    setResetToken((current) => current + 1);

    if (previousJobId) {
      void deleteComparison(previousJobId).catch(() => undefined);
    }
  };

  const handleRun = async () => {
    if (!uploadResult?.job_id) {
      setError("Сначала загрузите файлы и получите идентификатор задания.");
      return;
    }
    if (!key1) {
      setError("Выберите обязательный Ключ 1 перед запуском сравнения.");
      return;
    }

    setRunning(true);
    setError(null);

    try {
      await runComparison(uploadResult.job_id, {
        key1,
        key2: key2 || null,
        structure_only: structureOnly,
        check_field_order: checkFieldOrder,
      });
      const status = await getComparisonStatus(uploadResult.job_id);
      setComparisonStatus(status);
      setLastRunSignature(currentParamsSignature);
      setPreview(null);
      setPreviewOffset(0);
      if (!["queued", "processing"].includes(status.status)) {
        setRunning(false);
      }
    } catch (runError) {
      setRunning(false);
      setError(runError instanceof Error ? runError.message : "Ошибка запуска сравнения");
    }
  };

  const metrics = comparisonStatus?.summary;
  const isCompleted = comparisonStatus?.status === "completed";
  const isFailed = comparisonStatus?.status === "failed";
  const syntheticPreviewColumns = selectedCategoryRow?.syntheticRows?.[0]
    ? Object.keys(selectedCategoryRow.syntheticRows[0])
    : [];
  const filteredPreviewRows =
    preview && selectedCategoryRow?.previewFilter
      ? preview.rows.filter((row) => selectedCategoryRow.previewFilter?.(row.values) ?? true)
      : preview?.rows ?? [];
  const previewColumns = filteredPreviewRows[0]
    ? Object.keys(filteredPreviewRows[0].values)
    : preview?.rows[0]
      ? Object.keys(preview.rows[0].values)
      : syntheticPreviewColumns;
  const showPreviewPagination = Boolean(
    !selectedCategoryRow?.syntheticRows && preview && preview.total > preview.limit,
  );

  const handleDownload = async () => {
    if (!uploadResult?.job_id) {
      return;
    }
    setDownloadLoading(true);
    setError(null);
    try {
      const blob = await downloadComparisonReport(uploadResult.job_id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `comparison-${uploadResult.job_id}.xlsx`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : "Ошибка скачивания отчета");
    } finally {
      setDownloadLoading(false);
    }
  };

  return (
    <main className="workspace-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">DBF Comparator Pro</p>
          <h1>Строгая сверка DBF-файлов для внутреннего контура</h1>
          <p className="hero__copy">
            Загрузите два DBF-файла, дождитесь автоматического чтения структуры и сразу запускайте строгую проверку
            без нормализации значений.
          </p>
        </div>
        <div className="warning-banner">
          <strong>Важно:</strong> скрытые символы, пробелы и другие невидимые различия будут участвовать в проверке.
        </div>
      </section>

      <section className="workspace-grid">
        <div className="workspace-grid__main">
          <div className="file-grid">
            <div
              className="matched-panel"
              ref={file1PanelRef}
              style={matchedHeights.top ? { height: `${matchedHeights.top}px` } : undefined}
            >
              <FileUploadCard
                slotLabel="Файл 1"
                file={files.file1}
                helperText="Эталонный или исходный DBF"
                resetToken={resetToken}
                serverMeta={
                  uploadResult?.files[0]
                    ? { encoding: uploadResult.files[0].encoding, fieldsCount: uploadResult.files[0].fields.length }
                    : undefined
                }
                disabled={loading}
                onChange={(file) => setFiles((current) => ({ ...current, file1: file }))}
              />
            </div>
            <div
              className="matched-panel"
              ref={file2PanelRef}
              style={matchedHeights.top ? { height: `${matchedHeights.top}px` } : undefined}
            >
              <FileUploadCard
                slotLabel="Файл 2"
                file={files.file2}
                helperText="Проверяемый DBF для сверки"
                resetToken={resetToken}
                serverMeta={
                  uploadResult?.files[1]
                    ? { encoding: uploadResult.files[1].encoding, fieldsCount: uploadResult.files[1].fields.length }
                    : undefined
                }
                disabled={loading}
                onChange={(file) => setFiles((current) => ({ ...current, file2: file }))}
              />
            </div>
          </div>

          <div className="panel controls-panel" ref={controlsPanelRef}>
            <div className="panel__heading">
              <div>
                <p className="eyebrow">Настройка сравнения</p>
                <h2>Ключевые поля и параметры</h2>
              </div>
              {uploadResult ? <StatusBadge tone="positive">Структура считана</StatusBadge> : null}
            </div>

            <div className="controls-grid">
              <SelectField
                label="Ключ 1"
                value={key1}
                options={availableFields}
                required
                disabled={!uploadResult}
                onChange={setKey1}
              />
              <SelectField
                label="Ключ 2"
                value={key2}
                options={availableFields}
                disabled={!uploadResult}
                onChange={setKey2}
              />
            </div>

            <div className="toggle-grid">
              <label className="toggle-card">
                <div className="toggle-card__content">
                  <span>Только структура</span>
                  <small>Подготовить запуск без анализа значений строк.</small>
                </div>
                <span className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={structureOnly}
                    onChange={(event) => setStructureOnly(event.target.checked)}
                  />
                  <span className="toggle-switch__slider" />
                </span>
              </label>

              <label className="toggle-card">
                <div className="toggle-card__content">
                  <span>Проверка очередности полей</span>
                  <small>Учитывать порядок колонок при сравнении схемы.</small>
                </div>
                <span className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={checkFieldOrder}
                    onChange={(event) => setCheckFieldOrder(event.target.checked)}
                  />
                  <span className="toggle-switch__slider" />
                </span>
              </label>
            </div>
          </div>
        </div>

        <aside className="workspace-grid__side">
          <div
            className="panel action-panel"
            ref={actionPanelRef}
            style={matchedHeights.top ? { height: `${matchedHeights.top}px` } : undefined}
          >
            <p className="eyebrow">Статус загрузки</p>
            <h2>{uploadResult ? "Файлы готовы к запуску" : "Выберите оба файла"}</h2>
            <p>
              {loading
                ? "Считываем структуру DBF и подготавливаем поля для ключей."
                : uploadResult
                  ? "Структура считана. Можно сразу запускать проверку."
                  : "После выбора двух DBF структура прочитается автоматически, без отдельной кнопки."}
            </p>

            <div className="action-panel__buttons">
              <button className="button button--primary-alt" type="button" disabled={!canRun} onClick={handleRun}>
                {running ? "Сравнение выполняется..." : "Проверить"}
              </button>
              <button className="button button--primary-alt" type="button" disabled={!canDownload} onClick={handleDownload}>
                {downloadLoading ? "Подготовка..." : "Скачать Excel-отчет"}
              </button>
            </div>

            {error ? <p className="inline-error">{error}</p> : null}
          </div>

          <div
            className="panel summary-panel"
            ref={summaryPanelRef}
            style={matchedHeights.bottom ? { height: `${matchedHeights.bottom}px` } : undefined}
          >
            <p className="eyebrow">Текущая форма</p>
            <ul className="summary-list">
              <li>
                <span>Ключ 1</span>
                <strong>{key1 || "не выбран"}</strong>
              </li>
              <li>
                <span>Ключ 2</span>
                <strong>{key2 || "не выбран"}</strong>
              </li>
              <li>
                <span>Режим</span>
                <strong>{structureOnly ? "Только структура" : "Полное сравнение"}</strong>
              </li>
              <li>
                <span>Порядок полей</span>
                <strong>{checkFieldOrder ? "Проверяется" : "Не проверяется"}</strong>
              </li>
              <li>
                <span>Статус</span>
                <strong>
                  {loading
                    ? "чтение структуры"
                    : getJobStatusLabel(comparisonStatus?.status ?? uploadResult?.status ?? "draft")}
                </strong>
              </li>
            </ul>
          </div>
        </aside>
      </section>

      <section className="results-section">
        <div
          className={`panel results-banner ${
            isCompleted ? (metrics?.has_differences ? "results-banner--danger" : "results-banner--positive") : isFailed ? "results-banner--danger" : "results-banner--neutral"
          }`}
        >
          <div>
            <p className="eyebrow">Результат сравнения</p>
            <h2>
              {isCompleted
                ? metrics?.has_differences
                  ? "Расхождения найдены"
                  : "Критичных расхождений не найдено"
                : isFailed
                  ? "Сравнение завершилось ошибкой"
                  : comparisonStatus?.status === "queued" || comparisonStatus?.status === "processing"
                    ? "Сравнение выполняется"
                    : "Результат появится после запуска"}
            </h2>
          </div>
          <span
            className="results-banner__status"
          >
            <StatusBadge
              tone={
                isCompleted
                  ? metrics?.has_differences
                    ? "danger"
                    : "positive"
                  : isFailed
                    ? "danger"
                    : "neutral"
              }
            >
              {getJobStatusLabel(comparisonStatus?.status ?? "not_started")}
            </StatusBadge>
          </span>
        </div>

        {comparisonStatus?.warnings.length ? (
          <div className="panel info-panel">
            {comparisonStatus.warnings.map((warning) => (
              <p key={warning}>{warning}</p>
            ))}
          </div>
        ) : null}

        {comparisonStatus?.error_message ? (
          <ErrorPanel code={comparisonStatus.error_code} message={comparisonStatus.error_message} />
        ) : null}

        {metrics ? (
          <>
            <div className="panel categories-panel">
              <div className="panel__heading">
                <div>
                  <p className="eyebrow">Категории</p>
                  <h3>Сводка проверки</h3>
                </div>
              </div>
              <div className="categories-table">
                {categoryRows.map((row) => (
                  <button
                    key={row.id}
                    type="button"
                    className={`categories-table__row categories-table__row--button ${
                      selectedCategory === row.id ? "categories-table__row--active" : ""
                    }`}
                    onClick={() => {
                      setSelectedCategory(row.id);
                      setPreviewOffset(0);
                      setPreview(null);
                    }}
                  >
                    <div>
                      <strong>{row.label}</strong>
                    </div>
                    <StatusBadge tone={row.tone}>{row.value}</StatusBadge>
                  </button>
                ))}
              </div>
            </div>

            <div className="panel preview-panel">
              <div className="panel__heading">
                <div>
                  <p className="eyebrow">Детали</p>
                  <h3>{selectedCategoryRow?.label ?? "Категория"}</h3>
                </div>
                {selectedCategoryRow?.syntheticRows ? (
                  <StatusBadge tone={selectedCategoryRow.tone}>
                    {selectedCategoryRow.syntheticRows.length === 0 ? "Пусто" : `${selectedCategoryRow.syntheticRows.length} строк`}
                  </StatusBadge>
                ) : preview ? (
                  <StatusBadge tone="neutral">
                    {filteredPreviewRows.length === 0
                      ? "Пусто"
                      : `${preview.offset + 1}-${preview.offset + filteredPreviewRows.length} / ${filteredPreviewRows.length}`}
                  </StatusBadge>
                ) : null}
              </div>

              {!selectedCategoryRow?.syntheticRows && previewLoading ? <p>Загружаем детали категории…</p> : null}
              {previewError ? <p className="inline-error">{previewError}</p> : null}
              {!selectedCategoryRow?.syntheticRows && !previewLoading && !previewError && preview && filteredPreviewRows.length === 0 ? (
                <p className="empty-state">В выбранной категории пока нет записей.</p>
              ) : null}

              {selectedCategoryRow?.syntheticRows && selectedCategoryRow.syntheticRows.length > 0 ? (
                <div className="preview-table-shell">
                  <table className="preview-table">
                    <thead>
                      <tr>
                        {previewColumns.map((column) => (
                          <th key={column}>{getPreviewColumnLabel(column)}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {selectedCategoryRow.syntheticRows.map((row, index) => (
                        <tr key={`${selectedCategoryRow.id}-${index}`}>
                          {previewColumns.map((column) => (
                            <td key={column}>
                              <span className="preview-value" title={getPreviewCellTitle(column, row[column])}>
                                {formatPreviewCell(column, row[column])}
                              </span>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
              {selectedCategoryRow?.syntheticRows && selectedCategoryRow.syntheticRows.length === 0 ? (
                <p className="empty-state">В выбранной категории различий не найдено.</p>
              ) : null}
              {!selectedCategoryRow?.syntheticRows && !selectedCategoryRow?.previewSection ? (
                <p className="empty-state">Для этой категории достаточно итоговой сводки без отдельной таблицы деталей.</p>
              ) : null}

              {!selectedCategoryRow?.syntheticRows && !previewLoading && !previewError && preview && filteredPreviewRows.length > 0 ? (
                <>
                  <div className="preview-table-shell">
                    <table className="preview-table">
                      <thead>
                        <tr>
                          {previewColumns.map((column) => (
                            <th key={column}>{getPreviewColumnLabel(column)}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {filteredPreviewRows.map((row, index) => (
                          <tr key={`${preview.offset}-${index}`}>
                            {previewColumns.map((column) => (
                              <td key={column}>
                                <span className="preview-value" title={getPreviewCellTitle(column, row.values[column])}>
                                  {formatPreviewCell(column, row.values[column])}
                                </span>
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {showPreviewPagination ? (
                    <div className="preview-actions">
                      <button
                        className="button button--secondary"
                        type="button"
                        disabled={preview.offset === 0}
                        onClick={() => setPreviewOffset((current) => Math.max(0, current - preview.limit))}
                      >
                        Назад
                      </button>
                      <button
                        className="button button--secondary"
                        type="button"
                        disabled={preview.offset + preview.limit >= preview.total}
                        onClick={() => setPreviewOffset((current) => current + preview.limit)}
                      >
                        Далее
                      </button>
                    </div>
                  ) : null}
                </>
              ) : null}
            </div>
          </>
        ) : null}
      </section>
    </main>
  );
}

function formatPreviewCell(column: string, value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined) {
    return "";
  }
  if (column === "issue" && typeof value === "string") {
    return getIssueLabel(value);
  }
  if (column === "file" && typeof value === "string") {
    return getFileLabel(value);
  }
  if (typeof value === "string") {
    if (column === "key") {
      return value.trim();
    }
    return value.replace(/[\u0020\u00a0]+$/g, "");
  }
  return String(value);
}

function getPreviewColumnLabel(column: string) {
  const labels: Record<string, string> = {
    key: "Ключ",
    field: "Поле",
    file: "Файл",
    file1_type: "Тип в Файле 1",
    file2_type: "Тип в Файле 2",
    file1_value: "Значение в Файле 1",
    file2_value: "Значение в Файле 2",
    occurrences: "Количество",
    issue: "Тип расхождения",
    position: "Позиция",
    file1_field: "Поле в Файле 1",
    file2_field: "Поле в Файле 2",
    статус: "Статус",
    файл: "Файл",
    строк: "Строк",
    дубликаты: "Дубликатов",
  };

  return labels[column] ?? column;
}

function getIssueLabel(issue: string) {
  const labels: Record<string, string> = {
    missing_in_file2: "Отсутствует в Файле 2",
    extra_in_file2: "Есть только в Файле 2",
  };

  return labels[issue] ?? issue;
}

function getFileLabel(file: string) {
  const labels: Record<string, string> = {
    file1: "Файл 1",
    file2: "Файл 2",
  };

  return labels[file] ?? file;
}

function getJobStatusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: "черновик",
    uploaded: "структура считана",
    ready_for_run: "готово к проверке",
    queued: "в очереди",
    processing: "выполняется",
    completed: "выполнено",
    failed: "ошибка",
    not_started: "не запущено",
  };

  return labels[status] ?? status;
}

function getPreviewCellTitle(column: string, value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined) {
    return "";
  }
  if (column === "issue" && typeof value === "string") {
    return getIssueLabel(value);
  }
  if (column === "file" && typeof value === "string") {
    return getFileLabel(value);
  }
  return String(value);
}
