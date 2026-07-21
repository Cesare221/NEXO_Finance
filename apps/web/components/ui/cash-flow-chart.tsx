"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export type CashFlowPoint = {
  month: string;
  income: number;
  expense: number;
};

const currency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0
});

const compactCurrency = new Intl.NumberFormat("pt-BR", {
  notation: "compact",
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0
});

export function CashFlowChart({ data }: { data: CashFlowPoint[] }) {
  const strongestMonth = data.reduce<CashFlowPoint | null>((best, item) => {
    if (!best) return item;
    return item.income + item.expense > best.income + best.expense ? item : best;
  }, null);
  const hasMovement = data.some((item) => item.income !== 0 || item.expense !== 0);

  return (
    <div className="cashflow-chart-shell">
      <p className="sr-only">
        {hasMovement && strongestMonth
          ? `Comparativo mensal de receitas e despesas. ${strongestMonth.month} concentra a maior movimentação do período, com ${currency.format(strongestMonth.income)} em receitas e ${currency.format(strongestMonth.expense)} em despesas.`
          : "Comparativo mensal de receitas e despesas sem movimentações no período."}
      </p>
      <div className="cashflow-chart" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={280}>
          <AreaChart
            data={data}
            margin={{ top: 12, right: 8, left: 0, bottom: 0 }}
            accessibilityLayer
          >
            <defs>
              <linearGradient id="income-area" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--chart-income)" stopOpacity={0.28} />
                <stop offset="95%" stopColor="var(--chart-income)" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="expense-area" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--chart-expense)" stopOpacity={0.22} />
                <stop offset="95%" stopColor="var(--chart-expense)" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="var(--hairline)" strokeDasharray="3 5" />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "var(--muted)", fontSize: 12 }}
              dy={8}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "var(--muted)", fontSize: 11 }}
              tickFormatter={(value) => compactCurrency.format(Number(value))}
              width={62}
            />
            <Tooltip
              cursor={{ stroke: "var(--muted)", strokeDasharray: "3 3" }}
              formatter={(value, name) => [
                currency.format(Number(value)),
                name === "income" ? "Receitas" : "Despesas"
              ]}
              labelFormatter={(label) => `Mês: ${label}`}
              contentStyle={{
                border: "1px solid var(--hairline)",
                borderRadius: 8,
                backgroundColor: "var(--surface)",
                color: "var(--text)",
                boxShadow: "var(--shadow-soft)",
                fontSize: 13
              }}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              formatter={(value) => (value === "income" ? "Receitas" : "Despesas")}
              wrapperStyle={{ color: "var(--muted)", fontSize: 12, paddingTop: 10 }}
            />
            <Area
              type="monotone"
              dataKey="income"
              name="income"
              stroke="var(--chart-income)"
              strokeWidth={3}
              fill="url(#income-area)"
              dot={{ r: 3, fill: "var(--surface)", strokeWidth: 2 }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              dataKey="expense"
              name="expense"
              stroke="var(--chart-expense)"
              strokeWidth={2.5}
              strokeDasharray="7 4"
              fill="url(#expense-area)"
              dot={{ r: 3, fill: "var(--surface)", strokeWidth: 2 }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <table className="sr-only">
        <caption>Receitas e despesas por mês</caption>
        <thead><tr><th>Mês</th><th>Receitas</th><th>Despesas</th></tr></thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.month}>
              <th>{item.month}</th>
              <td>{currency.format(item.income)}</td>
              <td>{currency.format(item.expense)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
