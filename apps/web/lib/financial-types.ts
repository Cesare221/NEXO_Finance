export type DashboardAccount = {
  id: number;
  name: string;
  type: string;
  current_balance: string;
};

export type DashboardTransaction = {
  id: number;
  account_id: number;
  category_id: number | null;
  type: string;
  amount: string;
  description: string | null;
  occurred_on: string;
  origin: string;
};

export type DashboardStatement = {
  id: number;
  credit_card_id: number;
  due_on: string;
  total_amount: string;
  paid_amount: string;
  status: string;
};

export type DashboardCashFlowPoint = {
  month: string;
  income: string;
  expense: string;
};

export type DashboardData = {
  total_balance: string;
  period_income: string;
  period_expenses: string;
  open_statement_total: string;
  accounts: DashboardAccount[];
  open_statements: DashboardStatement[];
  upcoming_due: DashboardStatement[];
  recent_transactions: DashboardTransaction[];
  cash_flow: DashboardCashFlowPoint[];
};

export type FinancialAccount = {
  id: number;
  user_id: number;
  name: string;
  type: string;
  initial_balance: string;
  color: string | null;
  icon: string | null;
  is_archived: boolean;
};

export type FinancialCategory = {
  id: number;
  user_id: number;
  name: string;
  parent_id: number | null;
  color: string | null;
  icon: string | null;
  is_archived: boolean;
  children: FinancialCategory[];
};

export type DemoDatasetState = {
  active: boolean;
  version: string;
  installed_at: string | null;
  summary: {
    accounts: number;
    cards: number;
    categories: number;
    transactions: number;
    recurring_rules: number;
  };
};

export type CategoryDeleteResult = {
  action: "deleted" | "archived";
  category: FinancialCategory;
};

export type FinancialTransaction = {
  id: number;
  user_id: number;
  account_id: number;
  category_id: number | null;
  type: string;
  amount: string;
  description: string | null;
  occurred_on: string;
  origin: string;
  is_deleted: boolean;
};

export type FinancialCreditCard = {
  id: number;
  user_id: number;
  payment_account_id: number;
  name: string;
  limit_amount: string;
  closing_day: number;
  due_day: number;
  is_archived: boolean;
  used_limit: string;
  available_limit: string;
};
