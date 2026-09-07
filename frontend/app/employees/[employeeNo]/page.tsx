"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, formatDate, formatMoney, type EmployeeDetail } from "@/lib/api";

export default function EmployeePage() {
  const { employeeNo } = useParams<{ employeeNo: string }>();
  const [employee, setEmployee] = useState<EmployeeDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.employee(employeeNo).then(setEmployee).catch((e) => setError(e.message));
  }, [employeeNo]);

  if (error) return <p className="text-under">{error}</p>;
  if (!employee) return <p className="text-muted">Loading {employeeNo}…</p>;

  return (
    <div className="space-y-10">
      <Link href="/" className="text-sm text-muted underline underline-offset-4">
        Back to everyone
      </Link>

      <header className="border-b border-rule pb-8">
        <h1 className="text-2xl">{employee.name}</h1>
        <p className="pt-1 text-muted">
          {employee.job_title} · {employee.level} · {employee.department} ·{" "}
          {employee.country}
        </p>
        <div className="flex flex-wrap items-baseline gap-x-10 gap-y-3 pt-6">
          <div>
            <div className="figure text-3xl">{formatMoney(employee.current_salary)}</div>
            <div className="text-sm text-muted">Current salary, annual</div>
          </div>
          {employee.compa_ratio && (
            <div>
              <div
                className={`figure text-3xl ${
                  employee.band_position === "below"
                    ? "text-under"
                    : employee.band_position === "above"
                      ? "text-over"
                      : ""
                }`}
              >
                {employee.compa_ratio}
              </div>
              <div className="text-sm text-muted">
                Compa-ratio · {employee.band_position} band
              </div>
            </div>
          )}
        </div>
      </header>

      <section>
        <h2 className="pb-4 text-lg">Pay history</h2>
        <ol className="border-t border-rule">
          {[...employee.history].reverse().map((record, index) => (
            <li
              key={`${record.effective_from}-${index}`}
              className="flex flex-wrap items-baseline justify-between gap-2 border-b border-rule/60 py-3"
            >
              <span className="figure text-sm text-muted">
                {formatDate(record.effective_from)} —{" "}
                {record.effective_to ? formatDate(record.effective_to) : "present"}
              </span>
              <span className="text-sm text-muted">{record.reason.replace("_", " ")}</span>
              <span className="figure">{formatMoney(record.amount)}</span>
            </li>
          ))}
        </ol>
      </section>

      <RaiseForm employeeNo={employee.employee_no} onApplied={setEmployee} />
    </div>
  );
}

function RaiseForm({
  employeeNo,
  onApplied,
}: {
  employeeNo: string;
  onApplied: (employee: EmployeeDetail) => void;
}) {
  const [percent, setPercent] = useState("5");
  const [effectiveFrom, setEffectiveFrom] = useState("");
  const [reason, setReason] = useState("merit");
  const [problem, setProblem] = useState<string | null>(null);
  const [applying, setApplying] = useState(false);

  async function apply() {
    setApplying(true);
    setProblem(null);
    try {
      onApplied(
        await api.applyRaise(employeeNo, {
          percent,
          effective_from: effectiveFrom,
          reason,
        })
      );
    } catch (e) {
      setProblem((e as Error).message);
    } finally {
      setApplying(false);
    }
  }

  return (
    <section className="border-t border-rule pt-8">
      <h2 className="pb-4 text-lg">Give a raise</h2>
      <div className="flex flex-wrap items-end gap-4">
        <label className="text-sm">
          <span className="block pb-1 text-muted">Increase</span>
          <input
            type="number"
            min="0.1"
            max="100"
            step="0.1"
            value={percent}
            onChange={(event) => setPercent(event.target.value)}
            className="figure w-28 border border-rule bg-white px-3 py-2"
          />
        </label>
        <label className="text-sm">
          <span className="block pb-1 text-muted">Effective from</span>
          <input
            type="date"
            value={effectiveFrom}
            onChange={(event) => setEffectiveFrom(event.target.value)}
            className="figure border border-rule bg-white px-3 py-2"
          />
        </label>
        <label className="text-sm">
          <span className="block pb-1 text-muted">Reason</span>
          <select
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            className="border border-rule bg-white px-3 py-2"
          >
            <option value="merit">Merit</option>
            <option value="promotion">Promotion</option>
            <option value="market_adjustment">Market adjustment</option>
          </select>
        </label>
        <button
          type="button"
          onClick={apply}
          disabled={applying || !effectiveFrom}
          className="bg-ink px-4 py-2 text-sm text-paper disabled:opacity-40"
        >
          {applying ? "Applying…" : "Apply raise"}
        </button>
      </div>
      {problem && <p className="pt-4 text-sm text-under">{problem}</p>}
      <p className="pt-4 text-sm text-muted">
        The current salary closes the day before the new one starts. Nothing is
        overwritten.
      </p>
    </section>
  );
}
