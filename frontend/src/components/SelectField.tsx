type SelectFieldProps = {
  label: string;
  value: string;
  options: string[];
  required?: boolean;
  disabled?: boolean;
  onChange: (value: string) => void;
};

export function SelectField({ label, value, options, required, disabled, onChange }: SelectFieldProps) {
  return (
    <label className="select-field">
      <span>
        {label}
        {required ? " *" : ""}
      </span>
      <select value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
        <option value="">{disabled ? "Сначала загрузите файлы" : "Выберите поле"}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
