import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SelectField } from "./SelectField";


describe("SelectField", () => {
  it("renders options and propagates selection", () => {
    const onChange = vi.fn();
    render(<SelectField label="Ключ 1" value="" options={["ID", "ACC"]} onChange={onChange} />);

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "ACC" } });
    expect(onChange).toHaveBeenCalledWith("ACC");
  });
});
