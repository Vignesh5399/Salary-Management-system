"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  formatMoney,
  type EmployeeSummary,
  type Page,
  type Summary,
} from "@/lib/api";

const COUNTRIES = ["IN", "US", "GB", "SG", "AU"];
const DEPARTMENTS = [
  "Engineering",
  "Product",
  "Design",
  "Sales",
  "Marketing",
  "Finance",
  "People",
  "Support",
];

export default function Directory() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [page, setPage] = useState<Page | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [country, setCountry] = useState("");
  const [department, setDepartment] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.summary().then(setSummary).catch((e) => setError(e.message));
  }, []);

  const load = useCallback(async () => {
    const params = new URLSearchParams({ page: String(pageNumber), size: "25" });
    if (country) params.set("country", country);
    if (department) params.set("department", department);
    try {
      setPage(await api.employees(params));
    } catch (e) {
      setError((e as Error).message);
    }
  }, [pageNumber, country, department]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) {
    return (
      <p className="text-under">
        {error}. Check the API is running and NEXT_PUBLIC_API_URL points at it.
      </p>
    );
  }

  const pages = page ? Math.ceil(page.total / page.size) : 0;

  return (
    <div className="space-y-10">
      <section className="flex flex-wrap gap-x-14 gap-y-6 border-b border-rule pb-8">
        <Figure label="People" value={summary ? summary.headcount.toLocaleString() : "—"} />
        <Figure
          label="Annual payroll"
          value={summary ? formatMoney(summary.total_annual) : "—"}
        />
        <Figure
          label="Average"
          value={summary ? formatMoney(summary.average_annual) : "—"}
        />
        <Figure
          label="Paid below band"
          value={summary ? summary.below_band.toLocaleString() : "—"}
          alert={Boolean(summary && summary.below_band > 0)}
        />
      </section>

      <section className="flex flex-wrap items-end gap-4">
        <Select
          label="Country"
          value={country}
          options={COUNTRIES}
          onChange={(value) => {
            setCountry(value);
            setPageNumber(1);
          }}
        />
        <Select
          label="Department"
          value={department}
          options={DEPARTMENTS}
          onChange={(value) => {
            setDepartment(value);
            setPageNumber(1);
          }}
        />
        {(country || department) && (
          <button
            type="button"
            onClick={() => {
              setCountry("");
              setDepartment("");
              setPageNumber(1);
            }}
            className="pb-1 text-sm text-muted underline underline-offset-4 hover:text-ink"
          >
            Clear filters
          </button>
        )}
      </section>

      <section>
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule text-left text-muted">
              <th className="py-2 font-medium">Name</th>
              <th className="py-2 font-medium">Role</th>
              <th className="py-2 font-medium">Location</th>
              <th className="py-2 text-right font-medium">Salary</th>
              <th className="py-2 text-right font-medium">Compa-ratio</th>
            </tr>
          </thead>
          <tbody>
            {page?.items.map((employee) => (
              <Row key={employee.employee_no} employee={employee} />
            ))}
          </tbody>
        </table>

        {page && page.total === 0 && (
          <p className="py-10 text-muted">
            Nobody matches those filters. Clear them to see everyone.
          </p>
        )}

        {pages > 1 && (
          <nav className="flex items-center justify-between pt-6 text-sm">
            <button
              type="button"
              disabled={pageNumber === 1}
              onClick={() => setPageNumber((n) => n - 1)}
              className="text-muted underline underline-offset-4 enabled:hover:text-ink disabled:opacity-40"
            >
              Previous
            </button>
            <span className="figure text-muted">
              {pageNumber} of {pages.toLocaleString()}
            </span>
            <button
              type="button"
              disabled={pageNumber >= pages}
              onClick={() => setPageNumber((n) => n + 1)}
              className="text-muted underline underline-offset-4 enabled:hover:text-ink disabled:opacity-40"
            >
              Next
            </button>
          </nav>
        )}
      </section>
    </div>
  );
}

function Row({ employee }: { employee: EmployeeSummary }) {
  const outOfBand = employee.band_position && employee.band_position !== "within";
  return (
    <tr className="border-b border-rule/60">
      <td className="py-3">
        <Link
          href={`/employees/${employee.employee_no}`}
          className="underline decoration-rule underline-offset-4 hover:decoration-ink"
        >
          {employee.name}
        </Link>
      </td>
      <td className="py-3 text-muted">
        {employee.job_title} · {employee.level}
      </td>
      <td className="py-3 text-muted">
        {employee.country} · {employee.department}
      </td>
      <td className="figure py-3 text-right">{formatMoney(employee.current_salary)}</td>
      <td
        className={`figure py-3 text-right ${
          employee.band_position === "below"
            ? "text-under"
            : employee.band_position === "above"
              ? "text-over"
              : "text-muted"
        }`}
      >
        {employee.compa_ratio ?? "—"}
        {outOfBand && <span className="ml-2 text-xs">{employee.band_position}</span>}
      </td>
    </tr>
  );
}

function Figure({
  label,
  value,
  alert = false,
}: {
  label: string;
  value: string;
  alert?: boolean;
}) {
  return (
    <div>
      <div className={`figure text-2xl ${alert ? "text-under" : ""}`}>{value}</div>
      <div className="text-sm text-muted">{label}</div>
    </div>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-sm">
      <span className="block pb-1 text-muted">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="border border-rule bg-white px-3 py-2"
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
