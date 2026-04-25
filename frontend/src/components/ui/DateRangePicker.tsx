// components/ui/DateRangePicker.tsx

import { useEffect, useRef, useState } from "react";
import { DayPicker, type DateRange } from "react-day-picker";
import { format } from "date-fns";
import "react-day-picker/dist/style.css";

type Props = {
  range?: DateRange;
  onChange: (range?: DateRange) => void;
  variant?: "button" | "inline";
  numberOfMonths?: number;
  align?: "left" | "right";
};

export default function DateRangePicker({
  range,
  onChange,
  variant = "button",
  numberOfMonths = 1,
  align = "right",
}: Props) {
  const [open, setOpen] = useState(false);
  const [selectingTo, setSelectingTo] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setSelectingTo(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const picker = (
    <DayPicker
      mode="range"
      numberOfMonths={numberOfMonths}
      selected={range}
      onSelect={(r) => {
        // first click → from
        if (r?.from && !selectingTo) {
          setSelectingTo(true);
          onChange({ from: r.from, to: undefined });
          return;
        }

        // second click → to
        if (r?.from && r?.to && selectingTo) {
          onChange(r);
          setSelectingTo(false);
          setOpen(false);
        }
      }}
    />
  );

  if (variant === "inline") {
    return <div className="rounded-lg border bg-white p-3">{picker}</div>;
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => {
          setOpen((v) => !v);
          setSelectingTo(false);
        }}
        className="rounded-md border px-3 py-2 text-sm hover:bg-gray-50"
      >
        {range?.from && range?.to
          ? `${format(range.from, "dd MMM yyyy")} – ${format(
              range.to,
              "dd MMM yyyy",
            )}`
          : "Select date range"}
      </button>

      {open && (
        <div
          className={`absolute z-50 mt-2 rounded-lg border bg-white p-3 shadow-lg ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          {picker}
        </div>
      )}
    </div>
  );
}
