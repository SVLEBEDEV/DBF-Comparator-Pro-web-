import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FileUploadCard } from "./FileUploadCard";


describe("FileUploadCard", () => {
  it("renders server metadata and emits selected file", () => {
    const onChange = vi.fn();
    render(
      <FileUploadCard
        slotLabel="Файл 1"
        file={null}
        helperText="Тестовый helper"
        serverMeta={{ encoding: "cp866", fieldsCount: 3 }}
        onChange={onChange}
      />,
    );

    const input = screen.getByLabelText("Выберите DBF-файл") as HTMLInputElement;
    const file = new File(["abc"], "sample.dbf", { type: "application/octet-stream" });
    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText("Кодировка: cp866")).toBeInTheDocument();
    expect(screen.getByText("Поля: 3")).toBeInTheDocument();
    expect(onChange).toHaveBeenCalledWith(file);
  });
});
