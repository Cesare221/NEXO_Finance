"use client";

import { CalendarDays, Check, ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export type DateRange = {
  start: string;
  end: string;
};

type DateRangePickerProps = {
  value: DateRange;
  onChange: (value: DateRange) => void;
  disabled?: boolean;
};

const displayFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  timeZone: "UTC"
});

function isoDate(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function daysAgo(days: number) {
  const value = new Date();
  value.setDate(value.getDate() - days);
  return value;
}

function presetRange(preset: string): DateRange {
  const today = new Date();
  if (preset === "previous-month") {
    return {
      start: isoDate(new Date(today.getFullYear(), today.getMonth() - 1, 1)),
      end: isoDate(new Date(today.getFullYear(), today.getMonth(), 0))
    };
  }
  if (preset === "30-days") return { start: isoDate(daysAgo(29)), end: isoDate(today) };
  if (preset === "90-days") return { start: isoDate(daysAgo(89)), end: isoDate(today) };
  if (preset === "year") return { start: `${today.getFullYear()}-01-01`, end: isoDate(today) };
  return {
    start: isoDate(new Date(today.getFullYear(), today.getMonth(), 1)),
    end: isoDate(today)
  };
}

export function defaultDashboardPeriod() {
  return presetRange("current-month");
}

function rangeLabel(value: DateRange) {
  const start = displayFormatter.format(new Date(`${value.start}T00:00:00Z`)).replaceAll(".", "");
  const end = displayFormatter.format(new Date(`${value.end}T00:00:00Z`)).replaceAll(".", "");
  return start === end ? start : `${start} - ${end}`;
}

export function DateRangePicker({ value, onChange, disabled = false }: DateRangePickerProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(value);
  const [error, setError] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => setDraft(value), [value]);
  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);

  function choosePreset(preset: string) {
    const next = presetRange(preset);
    setDraft(next);
    setError("");
    onChange(next);
    setOpen(false);
  }

  function applyCustomRange() {
    if (!draft.start || !draft.end) {
      setError("Selecione as duas datas.");
      return;
    }
    const start = new Date(`${draft.start}T00:00:00Z`);
    const end = new Date(`${draft.end}T00:00:00Z`);
    const span = (end.getTime() - start.getTime()) / 86_400_000;
    if (span < 0) {
      setError("A data final deve ser posterior à inicial.");
      return;
    }
    if (span > 730) {
      setError("Escolha um período de até dois anos.");
      return;
    }
    setError("");
    onChange(draft);
    setOpen(false);
  }

  return (
    <div className="date-range-picker" ref={rootRef}>
      <button
        className="period-select"
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
      >
        <CalendarDays size={18} aria-hidden="true" />
        <span>{rangeLabel(value)}</span>
        <ChevronDown size={16} aria-hidden="true" />
      </button>
      {open ? (
        <div className="date-range-popover" role="dialog" aria-label="Selecionar período">
          <div className="date-range-presets" aria-label="Períodos rápidos">
            {[
              ["current-month", "Mês atual"],
              ["previous-month", "Mês anterior"],
              ["30-days", "Últimos 30 dias"],
              ["90-days", "Últimos 90 dias"],
              ["year", "Este ano"]
            ].map(([key, label]) => (
              <button key={key} type="button" onClick={() => choosePreset(key)}>{label}</button>
            ))}
          </div>
          <div className="date-range-custom">
            <label>
              Início
              <input
                type="date"
                value={draft.start}
                max={draft.end}
                onChange={(event) => setDraft((current) => ({ ...current, start: event.target.value }))}
              />
            </label>
            <label>
              Fim
              <input
                type="date"
                value={draft.end}
                min={draft.start}
                onChange={(event) => setDraft((current) => ({ ...current, end: event.target.value }))}
              />
            </label>
          </div>
          {error ? <p className="date-range-error" role="alert">{error}</p> : null}
          <button className="button date-range-apply" type="button" onClick={applyCustomRange}>
            <Check size={17} aria-hidden="true" /> Aplicar período
          </button>
        </div>
      ) : null}
    </div>
  );
}
