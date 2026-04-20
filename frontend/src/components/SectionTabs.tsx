import type { ComparisonCategory } from "../lib/api";
import { StatusBadge } from "./StatusBadge";

type SectionTabsProps = {
  categories: ComparisonCategory[];
  selectedSection: string;
  onSelect: (section: string) => void;
};

export function SectionTabs({ categories, selectedSection, onSelect }: SectionTabsProps) {
  return (
    <div className="categories-table">
      {categories.map((category) => (
        <button
          key={category.code}
          type="button"
          className={`categories-table__row categories-table__row--button ${
            selectedSection === category.code ? "categories-table__row--active" : ""
          }`}
          onClick={() => onSelect(category.code)}
        >
          <div>
            <strong>{category.label}</strong>
            <small>{category.code}</small>
          </div>
          <StatusBadge tone={category.status === "attention" ? "danger" : "positive"}>{String(category.count)}</StatusBadge>
        </button>
      ))}
    </div>
  );
}
