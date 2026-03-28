"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  Clock3,
  Loader2,
  ShoppingCart,
  Sparkles,
} from "lucide-react";
import { NavBar } from "@/components/common/nav-bar";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getTomorrowDate } from "@/lib/utils";
import type { MealHistoryResponse, MealPlanResponse } from "@/types";
import { CUISINE_COLORS, CUISINE_LABELS } from "@/types";

const DISH_ROLE_LABELS: Record<string, string> = {
  main_curry: "Main",
  side_dish: "Side",
  salad: "Salad",
  accompaniment: "Extra",
  eggs: "Eggs",
  carb: "Carb",
};

function getDishRoleLabel(role: string) {
  return DISH_ROLE_LABELS[role] ?? role.replaceAll("_", " ");
}

function formatHistoryDishName(dish: string) {
  return dish
    .replaceAll("_", " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export default function DashboardPage() {
  const [tomorrowPlan, setTomorrowPlan] = useState<MealPlanResponse | null>(null);
  const [candidatePlans, setCandidatePlans] = useState<MealPlanResponse[]>([]);
  const [recentHistory, setRecentHistory] = useState<MealHistoryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const tomorrow = getTomorrowDate();

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([
      api.planner.approved(tomorrow),
      api.planner.candidates(tomorrow),
      api.planner.history(7),
    ])
      .then(([approvedResult, candidatesResult, historyResult]) => {
        if (cancelled) return;

        setTomorrowPlan(
          approvedResult.status === "fulfilled" ? approvedResult.value : null
        );

        setCandidatePlans(
          candidatesResult.status === "fulfilled"
            ? candidatesResult.value.filter(
                (plan) => plan.status !== "approved"
              )
            : []
        );

        setRecentHistory(
          historyResult.status === "fulfilled" ? historyResult.value : []
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [tomorrow]);

  const hasApprovedPlan = Boolean(tomorrowPlan);
  const hasDraftPlans = !hasApprovedPlan && candidatePlans.length > 0;

  return (
    <div className="min-h-screen pb-24 md:pb-10">
      <div className="mx-auto max-w-6xl px-4 pb-12 pt-6 md:px-6 lg:px-8">
        <PageHeader title="Dashboard" />

        {loading ? (
          <section className="rounded-[2rem] border border-white/70 bg-white/78 p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading tomorrow&apos;s dashboard...
            </div>
          </section>
        ) : hasApprovedPlan && tomorrowPlan ? (
          <ApprovedState plan={tomorrowPlan} tomorrow={tomorrow} />
        ) : hasDraftPlans ? (
          <DraftState candidatePlans={candidatePlans} tomorrow={tomorrow} />
        ) : (
          <EmptyState />
        )}

        <section className="mt-8">
          <p className="mb-3 font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
            Recent meals
          </p>

          {recentHistory.length > 0 ? (
            <div className="overflow-hidden rounded-[1.6rem] border border-white/70 bg-white/78 shadow-[0_16px_40px_rgba(24,38,37,0.05)]">
              {recentHistory.slice(0, 4).map((entry, index) => (
                <article
                  key={`${entry.history_date}-${entry.id}`}
                  className={`px-4 py-3 ${index > 0 ? "border-t border-border/70" : ""}`}
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
                        <span className="inline-flex items-center gap-2">
                          <Clock3 className="h-3.5 w-3.5" />
                          {new Date(
                            entry.history_date + "T00:00:00"
                          ).toLocaleDateString("en-IN", {
                            weekday: "short",
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                        <Badge variant="outline" className="text-[10px]">
                          {entry.cuisine}
                        </Badge>
                      </div>
                      <p className="mt-2 text-sm font-medium leading-6 text-foreground">
                        {entry.dishes_cooked
                          .map(formatHistoryDishName)
                          .join(", ")}
                      </p>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Eggs: {entry.egg_style}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="rounded-[1.6rem] border border-dashed border-border/80 bg-[rgba(244,244,239,0.62)] p-5 text-sm leading-6 text-muted-foreground">
              Recent meals will appear here after the first approved plan.
            </div>
          )}
        </section>
      </div>

      <NavBar />
    </div>
  );
}

function ApprovedState({
  plan,
  tomorrow,
}: {
  plan: MealPlanResponse;
  tomorrow: string;
}) {
  return (
    <section className="rounded-[2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(247,246,241,0.88))] p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
      <div className="max-w-4xl">
        <div className="flex items-center gap-2 text-emerald-700">
          <Check className="h-4 w-4" />
          <span className="text-sm font-medium">Plan approved</span>
        </div>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
          Open the cook brief, check shopping, or review the plan.
        </p>

        <div className="mt-6 rounded-[1.6rem] border border-emerald-200 bg-emerald-50/80 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              className={
                CUISINE_COLORS[plan.template_id] || "bg-zinc-100 text-zinc-800"
              }
            >
              {CUISINE_LABELS[plan.template_id] || plan.cuisine}
            </Badge>
            <span className="text-xs text-emerald-700/80">
              {plan.dishes.length} dishes
            </span>
          </div>
          <div className="mt-4 space-y-2">
            {plan.dishes.slice(0, 3).map((dish) => (
              <div
                key={dish.recipe_id}
                className="flex items-center justify-between gap-3 text-sm text-emerald-900"
              >
                <span className="font-medium">{dish.name}</span>
                <span className="text-xs text-emerald-700/80">
                  {getDishRoleLabel(dish.role)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <Button
            asChild
            size="lg"
            className="h-12 w-full rounded-full px-6 sm:w-auto"
          >
            <Link href={`/brief/${plan.id}`}>
              Open Cook Brief
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="h-11 w-full rounded-full border-white/80 bg-white/80 sm:w-auto"
          >
            <Link href={`/shopping/${plan.id}`}>
              <ShoppingCart className="mr-2 h-4 w-4" />
              Shopping
            </Link>
          </Button>
          <Link
            href={`/plans?date=${tomorrow}`}
            className="inline-flex h-11 items-center px-1 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            View Plan
          </Link>
        </div>
      </div>
    </section>
  );
}

function DraftState({
  candidatePlans,
  tomorrow,
}: {
  candidatePlans: MealPlanResponse[];
  tomorrow: string;
}) {
  return (
    <section className="rounded-[2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(247,246,241,0.88))] p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
      <div className="max-w-5xl">
        <div className="flex items-center gap-2 text-amber-700">
          <Sparkles className="h-4 w-4" />
          <span className="text-sm font-medium">Plan options ready</span>
        </div>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
          Review the options and approve one for tomorrow.
        </p>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {candidatePlans.slice(0, 3).map((plan, index) => (
            <article
              key={plan.id}
              className="rounded-[1.4rem] border border-border/80 bg-[rgba(245,245,239,0.72)] p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-muted-foreground">
                  Option {index + 1}
                </p>
                <span className="rounded-full bg-white/90 px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                  {CUISINE_LABELS[plan.template_id] || plan.cuisine}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-foreground">
                {plan.rationale}
              </p>
            </article>
          ))}
        </div>

        <div className="mt-6">
          <Button asChild size="lg" className="h-12 rounded-full px-6">
            <Link href={`/plans?date=${tomorrow}`}>
              Review options
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <section className="rounded-[2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(247,246,241,0.88))] p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
      <div className="max-w-2xl">
        <p className="text-lg font-medium leading-7 tracking-tight text-foreground">
          Capture leftovers and what needs using soon, then generate tomorrow&apos;s
          plan.
        </p>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <Button asChild size="lg" className="h-12 rounded-full px-6">
            <Link href="/checkin">
              Start Check-in
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
