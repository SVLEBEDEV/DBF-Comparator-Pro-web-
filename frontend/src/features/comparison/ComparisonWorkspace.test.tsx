import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ComparisonWorkspace } from "./ComparisonWorkspace";


describe("ComparisonWorkspace", () => {
  it("renders strict comparison warning and disabled primary actions before upload", () => {
    vi.stubGlobal("fetch", vi.fn());
    render(<ComparisonWorkspace />);

    expect(screen.getByText(/скрытые символы, пробелы/i)).toBeInTheDocument();
    expect(screen.getByText(/структура прочитается автоматически/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Проверить" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Скачать Excel-отчет" })).toBeDisabled();
  });
});
