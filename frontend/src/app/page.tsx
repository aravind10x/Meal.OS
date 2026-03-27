"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  ChefHat,
  Check,
  ClipboardList,
  Clock3,
  Loader2,
  Mic,
  ShoppingCart,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavBar } from "@/components/common/nav-bar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getTomorrowDate } from "@/lib/utils";
import type { MealHistoryResponse, MealPlanResponse } from "@/types";
import { CUISINE_COLORS, CUISINE_LABELS } from "@/types";

const WORKFLOW_STEPS: {
  number: string;
  title: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    number: "01",
    title: "Nightly check-in",
    description:
      "Capture leftovers, available vegetables, and what needs using soon before the household goes to bed.",
    icon: CalendarDays,
  },
  {
    number: "02",
    title: "Compare plans",
    description:
      "Review multiple AI-generated meal strategies with rationale, balance, and shopping impact in one place.",
    icon: Sparkles,
  },
  {
    number: "03",
    title: "Cook handoff",
    description:
      "Turn the approved plan into a cook brief, Hindi voice note, and shopping delta that can be acted on in the morning.",
    icon: ChefHat,
  },
];

const OUTPUT_PREVIEWS: {
  title: string;
  description: string;
  detail: string;
  icon: LucideIcon;
}[] = [
  {
    title: "Plan Options",
    description: "Three distinct meal directions grounded in vegetables, leftovers, and recent meal history.",
    detail: "Decision support, not just recipe search.",
    icon: Sparkles,
  },
  {
    title: "Cook Brief",
    description: "A structured handoff artifact with the menu, notes, and execution details ready to share.",
    detail: "Designed to be screenshot- and WhatsApp-ready.",
    icon: ClipboardList,
  },
  {
    title: "Shopping Delta",
    description: "Only the ingredients that are still missing, separated from likely-available and pantry items.",
    detail: "Keeps morning shopping focused and minimal.",
    icon: ShoppingCart,
  },
];

export default function HomePage() {
  const [tomorrowPlan, setTomorrowPlan] = useState<MealPlanResponse | null>(null);
  const [recentHistory, setRecentHistory] = useState<MealHistoryResponse[]>([]);
  const [loadingPlan, setLoadingPlan] = useState(true);
  const tomorrow = getTomorrowDate();

  useEffect(() => {
    api.planner
      .approved(tomorrow)
      .then((plan) => {
        if (plan) setTomorrowPlan(plan);
      })
      .catch(() => {})
      .finally(() => setLoadingPlan(false));

    api.planner
      .history(7)
      .then(setRecentHistory)
      .catch(() => {});
  }, [tomorrow]);

  return (
    <div className="min-h-screen pb-24 md:pb-10">
      <div className="mx-auto max-w-6xl px-4 pb-10 pt-6 md:px-6 lg:px-8">
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
          <div className="rounded-[2.2rem] border border-white/70 bg-[linear-gradient(155deg,rgba(255,255,255,0.96),rgba(245,245,239,0.88))] px-6 py-7 shadow-[0_30px_80px_rgba(24,38,37,0.1)] md:px-9 md:py-10">
            <p className="font-mono text-[0.72rem] uppercase tracking-[0.28em] text-muted-foreground">
              AI household meal operating system
            </p>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-foreground md:text-5xl">
              Meal.OS
            </h1>
            <p className="mt-5 max-w-3xl text-2xl font-semibold leading-tight tracking-[-0.03em] text-foreground md:text-[2.8rem] md:leading-[1.03]">
              Tonight&apos;s 60-second check-in becomes tomorrow&apos;s cooking plan.
            </p>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground md:text-base">
              Built for Indian households coordinating meals with a cook:
              compare AI-generated options, approve one, and hand off a brief
              plus shopping delta before morning.
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Leftovers
              </Badge>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Vegetables
              </Badge>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                AI plans
              </Badge>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Cook brief
              </Badge>
              <Badge variant="secondary" className="rounded-full px-3 py-1">
                Shopping delta
              </Badge>
            </div>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg" className="h-12 rounded-full px-6">
                <Link href="/checkin">
                  Plan Tomorrow&apos;s Meals
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="h-12 rounded-full border-white/70 bg-white/70 px-6"
              >
                <Link href="/recipes">Recipe Library</Link>
              </Button>
            </div>
          </div>

          <aside className="rounded-[2.2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(247,246,241,0.88))] p-6 shadow-[0_24px_70px_rgba(24,38,37,0.08)]">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                  Tomorrow Morning
                </p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                  Cook-ready outputs
                </h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Meal.OS packages the decision into something the household can
                  actually run before the kitchen starts.
                </p>
              </div>
              <Badge
                variant="outline"
                className="rounded-full border-emerald-200 bg-emerald-50 px-3 py-1 text-emerald-700"
              >
                Operational
              </Badge>
            </div>

            {loadingPlan ? (
              <div className="mt-8 flex items-center justify-center gap-2 rounded-[1.5rem] border border-dashed border-border/80 bg-white/55 px-4 py-8 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading tomorrow&apos;s status...
              </div>
            ) : tomorrowPlan ? (
              <div className="mt-6 space-y-4">
                <div className="rounded-[1.6rem] border border-emerald-200 bg-emerald-50/80 p-4">
                  <div className="flex items-center gap-2 text-emerald-700">
                    <Check className="h-4 w-4" />
                    <span className="text-sm font-medium">
                      Tomorrow&apos;s plan is approved
                    </span>
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <Badge
                      className={
                        CUISINE_COLORS[tomorrowPlan.template_id] ||
                        "bg-zinc-100 text-zinc-800"
                      }
                    >
                      {CUISINE_LABELS[tomorrowPlan.template_id] ||
                        tomorrowPlan.cuisine}
                    </Badge>
                    <span className="text-xs text-emerald-700/80">
                      {tomorrowPlan.dishes.length} dishes selected
                    </span>
                  </div>
                  <div className="mt-3 space-y-2">
                    {tomorrowPlan.dishes.slice(0, 3).map((dish) => (
                      <div
                        key={dish.recipe_id}
                        className="flex items-center justify-between gap-3 text-sm text-emerald-900"
                      >
                        <span className="font-medium">{dish.name}</span>
                        <span className="text-xs text-emerald-700/80">
                          {dish.role.replaceAll("_", " ")}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-2 sm:grid-cols-2">
                  <Button
                    asChild
                    variant="outline"
                    className="h-11 w-full rounded-full border-white/80 bg-white/70"
                  >
                    <Link href={`/brief/${tomorrowPlan.id}`}>
                      <ChefHat className="mr-2 h-4 w-4" />
                      Cook Brief
                    </Link>
                  </Button>
                  <Button
                    asChild
                    variant="outline"
                    className="h-11 w-full rounded-full border-white/80 bg-white/70"
                  >
                    <Link href={`/shopping/${tomorrowPlan.id}`}>
                      <ShoppingCart className="mr-2 h-4 w-4" />
                      Shopping
                    </Link>
                  </Button>
                </div>
              </div>
            ) : (
              <div className="mt-6 space-y-3">
                <div className="rounded-[1.6rem] border border-border/80 bg-white/75 p-4">
                  <p className="font-mono text-[0.7rem] uppercase tracking-[0.24em] text-muted-foreground">
                    Awaiting approval
                  </p>
                  <p className="mt-2 text-lg font-semibold tracking-tight text-foreground">
                    No approved plan yet
                  </p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    Tonight&apos;s decision will show up here as a complete
                    morning-ready package.
                  </p>
                </div>

                <div className="space-y-2 rounded-[1.6rem] border border-border/80 bg-[rgba(241,243,238,0.72)] p-4">
                  <StatusLine
                    icon={Sparkles}
                    label="Three meal options generated"
                    detail="Different approaches, one household decision."
                  />
                  <StatusLine
                    icon={Mic}
                    label="Cook brief + Hindi voice note"
                    detail="Ready for handoff once a plan is approved."
                  />
                  <StatusLine
                    icon={ShoppingCart}
                    label="Only the missing ingredients"
                    detail="Shopping stays focused on the delta."
                  />
                </div>
              </div>
            )}
          </aside>
        </section>

        <section className="mt-6 rounded-[2rem] border border-white/70 bg-white/75 p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                How The Household Runs Tomorrow
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                One calm flow from kitchen check-in to cook handoff.
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              The point is not more planning. The point is finishing tomorrow&apos;s
              meal decisions while everyone still has a minute tonight.
            </p>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {WORKFLOW_STEPS.map((step) => (
              <article
                key={step.number}
                className="rounded-[1.6rem] border border-border/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.88),rgba(244,244,239,0.72))] p-5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[0.78rem] uppercase tracking-[0.24em] text-muted-foreground">
                    {step.number}
                  </span>
                  <step.icon className="h-4 w-4 text-primary" />
                </div>
                <h3 className="mt-4 text-lg font-semibold tracking-tight text-foreground">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {step.description}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-6 rounded-[2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(246,245,240,0.88),rgba(255,255,255,0.82))] p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                What Meal.OS Produces
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                Artifacts your household can actually use.
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              The strongest part of the system is what comes out the other side:
              concrete outputs that reduce one more morning decision.
            </p>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {OUTPUT_PREVIEWS.map((item) => (
              <article
                key={item.title}
                className="rounded-[1.6rem] border border-border/80 bg-white/78 p-5"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-secondary text-primary">
                    <item.icon className="h-4 w-4" />
                  </div>
                  <h3 className="text-lg font-semibold tracking-tight text-foreground">
                    {item.title}
                  </h3>
                </div>
                <p className="mt-4 text-sm leading-6 text-muted-foreground">
                  {item.description}
                </p>
                <p className="mt-4 text-sm font-medium text-foreground">
                  {item.detail}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-6 rounded-[2rem] border border-white/70 bg-white/75 p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                Household Memory
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                The system keeps a usable record of meal rhythm.
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              Recent history helps the planner avoid repetition and keep variety
              visible, without forcing the household to remember what happened
              last week.
            </p>
          </div>

          {recentHistory.length > 0 ? (
            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {recentHistory.slice(0, 4).map((entry) => (
                <article
                  key={`${entry.history_date}-${entry.id}`}
                  className="rounded-[1.5rem] border border-border/80 bg-[rgba(244,244,239,0.74)] p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
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
                  <p className="mt-4 text-base font-semibold tracking-tight text-foreground">
                    {entry.dishes_cooked.join(", ")}
                  </p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Egg style: {entry.egg_style}
                  </p>
                </article>
              ))}
            </div>
          ) : (
            <div className="mt-6 rounded-[1.6rem] border border-dashed border-border/80 bg-[rgba(244,244,239,0.62)] p-5 text-sm leading-6 text-muted-foreground">
              Meal history will start filling in after the first approved plan.
            </div>
          )}
        </section>
      </div>

      <NavBar />
    </div>
  );
}

function StatusLine({
  icon: Icon,
  label,
  detail,
}: {
  icon: LucideIcon;
  label: string;
  detail: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-[1.2rem] border border-white/70 bg-white/78 p-3">
      <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-2xl bg-secondary text-primary">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="mt-1 text-xs leading-5 text-muted-foreground">
          {detail}
        </p>
      </div>
    </div>
  );
}
