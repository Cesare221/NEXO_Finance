"use client";

type CurrencyInputProps = {
  id: string;
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  error?: string;
  describedBy?: string;
  disabled?: boolean;
  required?: boolean;
};

const brlFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL"
});

function formatDecimal(value: string) {
  const amount = Number(value);
  return brlFormatter.format(Number.isFinite(amount) ? amount : 0);
}

export function CurrencyInput({
  id,
  label,
  value,
  onValueChange,
  error,
  describedBy,
  disabled,
  required
}: CurrencyInputProps) {
  const errorId = `${id}-error`;
  const ariaDescribedBy = [describedBy, error ? errorId : null].filter(Boolean).join(" ") || undefined;

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        className="input currency-input"
        id={id}
        inputMode="numeric"
        autoComplete="off"
        value={formatDecimal(value)}
        onChange={(event) => {
          const digits = event.target.value.replace(/\D/g, "");
          const cents = Number(digits || "0");
          onValueChange((cents / 100).toFixed(2));
        }}
        aria-invalid={Boolean(error)}
        aria-describedby={ariaDescribedBy}
        disabled={disabled}
        required={required}
      />
      {error && <span className="field-error" id={errorId}>{error}</span>}
    </div>
  );
}
