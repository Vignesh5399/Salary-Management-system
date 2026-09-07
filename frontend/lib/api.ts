const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Money = { amount: string; currency: string };

export type EmployeeSummary = {
  employee_no: string;
  name: string;
  country: string;
  department: string;
  level: string;
  job_title: string;
  current_salary: Money;
  band_position: "below" | "within" | "above" | null;
  compa_ratio: string | null;
};

export type CompensationRecord = {
  amount: Money;
  effective_from: string;
  effective_to: string | null;
  reason: string;
};

export type EmployeeDetail = EmployeeSummary & {
  email: string;
  hire_date: string;
  history: CompensationRecord[];
};

export type Page = {
  items: EmployeeSummary[];
  total: number;
  page: number;
  size: number;
};

export type GroupTotal = { group: string; headcount: number; total_annual: Money };

export type Summary = {
  headcount: number;
  total_annual: Money;
  average_annual: Money;
  below_band: number;
  by_country: GroupTotal[];
  by_department: GroupTotal[];
};

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) throw new Error(await errorText(response));
  return response.json();
}

async function errorText(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail ?? `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

export const api = {
  employees: (params: URLSearchParams) => get<Page>(`/api/employees?${params}`),
  employee: (employeeNo: string) => get<EmployeeDetail>(`/api/employees/${employeeNo}`),
  summary: () => get<Summary>("/api/analytics"),
  applyRaise: async (
    employeeNo: string,
    body: { percent: string; effective_from: string; reason: string }
  ): Promise<EmployeeDetail> => {
    const response = await fetch(`${BASE}/api/employees/${employeeNo}/raises`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(await errorText(response));
    return response.json();
  },
};

export function formatMoney(money: Money): string {
  const amount = Number(money.amount);
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: money.currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
