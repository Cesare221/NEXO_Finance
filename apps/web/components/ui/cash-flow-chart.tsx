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
                <stop offset="5%" stopColor="#176b60" stopOpacity={0.28} />
                <stop offset="95%" stopColor="#176b60" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="expense-area" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#b85d45" stopOpacity={0.22} />
                <stop offset="95%" stopColor="#b85d45" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="#dedbd2" strokeDasharray="3 5" />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#68665f", fontSize: 12 }}
              dy={8}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#68665f", fontSize: 11 }}
              tickFormatter={(value) => compactCurrency.format(Number(value))}
              width={62}
            />
            <Tooltip
              cursor={{ stroke: "#8e8a80", strokeDasharray: "3 3" }}
              formatter={(value, name) => [
                currency.format(Number(value)),
                name === "income" ? "Receitas" : "Despesas"
              ]}
              labelFormatter={(label) => `Mês: ${label}`}
              contentStyle={{
                border: "1px solid #dedbd2",
                borderRadius: 8,
                boxShadow: "0 10px 30px rgba(20, 20, 20, 0.1)",
                fontSize: 13
              }}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              formatter={(value) => (value === "income" ? "Receitas" : "Despesas")}
              wrapperStyle={{ fontSize: 12, paddingTop: 10 }}
            />
            <Area
              type="monotone"
              dataKey="income"
              name="income"
              stroke="#176b60"
              strokeWidth={3}
              fill="url(#income-area)"
              dot={{ r: 3, fill: "#ffffff", strokeWidth: 2 }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              dataKey="expense"
              name="expense"
              stroke="#b85d45"
              strokeWidth={2.5}
              fill="url(#expense-area)"
              dot={{ r: 3, fill: "#ffffff", strokeWidth: 2 }}
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
