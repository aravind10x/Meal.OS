"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { NavBar } from "@/components/common/nav-bar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import {
  ArrowLeftRight,
  Check,
  ChefHat,
  Loader2,
  ShoppingCart,
  Sparkles,
  UtensilsCrossed,
  Baby,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { MealPlanResponse, SwapOptionItem, DishEntry } from "@/types";
import { CUISINE_LABELS, CUISINE_COLORS, PROTEIN_LABELS } from "@/types";

function formatDate(dateStr: string): string {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-IN", {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
}

const ROLE_LABELS: Record<string, string> = {
  main_curry: "Main",
  main: "Main",
  side_dish: "Side",
  side: "Side",
  curry: "Curry",
  carb: "Carb",
  eggs: "Eggs",
  salad: "Salad",
  accompaniment: "Extra",
};

const ROLE_EMOJI: Record<string, string> = {
  main_curry: "🍛",
  main: "🍛",
  curry: "🍛",
  side_dish: "🥗",
  side: "🥗",
  salad: "🥬",
  carb: "🍚",
  eggs: "🥚",
  accompaniment: "🫙",
};

function getMissingIngredients(plan: MealPlanResponse): string[] {
  return plan.shopping_list
    .filter((item) => (item as Record<string, string>).category === "needed")
    .map((item) => (item as Record<string, string>).name);
}

export default function PlansPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const dateParam = searchParams.get("date");

  const [plans, setPlans] = useState<MealPlanResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState<number | null>(null);
  const [approvedPlan, setApprovedPlan] = useState<MealPlanResponse | null>(
    null
  );

  // Swap sheet state
  const [swapSheetOpen, setSwapSheetOpen] = useState(false);
  const [swapTarget, setSwapTarget] = useState<{
    planId: number;
    dish: DishEntry;
  } | null>(null);
  const [swapOptions, setSwapOptions] = useState<SwapOptionItem[]>([]);
  const [loadingSwapOptions, setLoadingSwapOptions] = useState(false);
  const [swapping, setSwapping] = useState(false);

  // Curd rice toggle state
  const [togglingCurdRice, setTogglingCurdRice] = useState(false);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        // Prefer fresh draft candidates when they exist for this date.
        const data = await api.planner.candidates(dateParam ?? undefined);
        if (data.length > 0) {
          setPlans(data);
          setApprovedPlan(null);
          return;
        }

        // Fall back to the approved plan when there are no drafts to review.
        if (dateParam) {
          const approved = await api.planner.approved(dateParam);
          if (approved) {
            setApprovedPlan(approved);
          }
        }
      } catch {
        toast.error("Failed to load meal plans");
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, [dateParam]);

  const handleApprove = async (planId: number) => {
    setApproving(planId);
    try {
      const result = await api.planner.approve(planId);
      setApprovedPlan(result.plan);
      toast.success("Meal plan approved!");
    } catch {
      toast.error("Failed to approve plan");
    } finally {
      setApproving(null);
    }
  };

  const handleOpenSwap = useCallback(
    async (planId: number, dish: DishEntry) => {
      setSwapTarget({ planId, dish });
      setSwapSheetOpen(true);
      setLoadingSwapOptions(true);
      try {
        const options = await api.planner.swapOptions(planId, dish.recipe_id);
        setSwapOptions(options);
      } catch {
        toast.error("Failed to load alternatives");
        setSwapOptions([]);
      } finally {
        setLoadingSwapOptions(false);
      }
    },
    []
  );

  const handleSelectSwap = useCallback(
    async (option: SwapOptionItem) => {
      if (!swapTarget) return;
      setSwapping(true);
      try {
        const updated = await api.planner.swap({
          plan_id: swapTarget.planId,
          old_recipe_id: swapTarget.dish.recipe_id,
          new_recipe_id: option.id,
          new_recipe_name: option.name,
          new_role: swapTarget.dish.role,
        });
        setPlans((prev) =>
          prev.map((p) => (p.id === updated.id ? updated : p))
        );
        toast.success(`Swapped to ${option.name}`);
        setSwapSheetOpen(false);
      } catch {
        toast.error("Failed to swap dish");
      } finally {
        setSwapping(false);
      }
    },
    [swapTarget]
  );

  const handleToggleCurdRice = useCallback(
    async (planId: number, currentValue: boolean) => {
      setTogglingCurdRice(true);
      try {
        const updated = await api.planner.toggleCurdRice(
          planId,
          !currentValue
        );
        setPlans((prev) =>
          prev.map((p) => (p.id === updated.id ? updated : p))
        );
        toast.success(
          !currentValue
            ? "Optional curd rice side added"
            : "Optional curd rice side removed"
        );
      } catch {
        toast.error("Failed to update plan");
      } finally {
        setTogglingCurdRice(false);
      }
    },
    []
  );

  if (loading) {
    return (
      <div className="min-h-screen pb-20">
        <div className="mx-auto max-w-6xl px-4 pt-6 md:px-6 lg:px-8">
          <PageHeader title="Plans" />
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
          </div>
        </div>
        <NavBar />
      </div>
    );
  }

  // Approved state
  if (approvedPlan) {
    return (
      <div className="min-h-screen pb-20">
        <div className="mx-auto max-w-6xl px-4 pt-6 md:px-6 lg:px-8">
          <PageHeader
            title="Plans"
            subtitle={formatDate(approvedPlan.plan_date)}
          />

          <section className="rounded-[1.8rem] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(247,246,241,0.88))] p-5 shadow-[0_16px_40px_rgba(24,38,37,0.05)]">
            <div className="flex items-center gap-2 text-emerald-700">
              <Check className="h-4 w-4" />
              <span className="text-sm font-medium">Approved</span>
            </div>
            <div className="mt-4 rounded-[1.4rem] border border-emerald-200 bg-emerald-50/80 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge
                  className={
                    CUISINE_COLORS[approvedPlan.template_id] ||
                    "bg-zinc-100 text-zinc-800"
                  }
                >
                  {CUISINE_LABELS[approvedPlan.template_id] ||
                    approvedPlan.cuisine}
                </Badge>
                <span className="text-xs text-emerald-700/80">
                  {approvedPlan.dishes.length} dishes
                </span>
              </div>
              <div className="mt-4">
                <PlanSummary plan={approvedPlan} />
              </div>
            </div>

            <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Button
                className="h-12 rounded-xl gap-2 sm:w-auto"
                onClick={() =>
                  router.push(`/brief/${approvedPlan.id}`)
                }
              >
                <ChefHat className="h-4 w-4" />
                Open Cook Brief
              </Button>
              <Button
                variant="outline"
                className="rounded-xl gap-2 sm:w-auto"
                onClick={() =>
                  router.push(`/shopping/${approvedPlan.id}`)
                }
              >
                <ShoppingCart className="h-4 w-4" />
                Shopping
              </Button>
            </div>
          </section>
        </div>
        <NavBar />
      </div>
    );
  }

  // No plans
  if (plans.length === 0) {
    return (
      <div className="min-h-screen pb-20">
        <div className="mx-auto max-w-6xl px-4 pt-6 md:px-6 lg:px-8">
          <PageHeader title="Plans" />
          <Card className="p-8 text-center">
            <Sparkles className="h-10 w-10 text-zinc-300 mx-auto mb-3" />
            <p className="text-sm text-zinc-400 mb-4">
              Start with check-in to generate plan options.
            </p>
            <Button onClick={() => router.push("/checkin")} className="gap-2">
              <UtensilsCrossed className="h-4 w-4" />
              Open Check-in
            </Button>
          </Card>
        </div>
        <NavBar />
      </div>
    );
  }

  // Plan selection
  return (
    <div className="min-h-screen pb-20">
      <div className="mx-auto max-w-6xl px-4 pt-6 md:px-6 lg:px-8">
        <PageHeader
          title="Plans"
          subtitle={dateParam ? formatDate(dateParam) : "Tomorrow"}
        />

        <Tabs defaultValue={`plan-${plans[0]?.id}`} className="w-full">
          <TabsList className="mb-4 grid h-auto w-full items-stretch gap-2 bg-transparent p-0 group-data-[orientation=horizontal]/tabs:h-auto md:grid-cols-3">
            {plans.map((plan, i) => {
              const missingIngredients = getMissingIngredients(plan);
              const hasViolations = plan.validation && !plan.validation.is_valid;

              return (
                <TabsTrigger
                  key={plan.id}
                  value={`plan-${plan.id}`}
                  className="h-auto min-w-0 items-start justify-start whitespace-normal rounded-[1.5rem] border border-white/70 bg-white/70 px-4 py-4 text-left data-[state=active]:border-primary/30 data-[state=active]:bg-white data-[state=active]:shadow-[0_14px_34px_rgba(24,38,37,0.08)]"
                >
                  <div className="w-full">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-muted-foreground">
                        Option {i + 1}
                      </span>
                      <Badge
                        className={
                          CUISINE_COLORS[plan.template_id] ||
                          "bg-zinc-100 text-zinc-800"
                        }
                      >
                        {CUISINE_LABELS[plan.template_id] || plan.cuisine}
                      </Badge>
                    </div>
                    <p className="mt-3 text-sm font-medium leading-5 text-zinc-900">
                      {plan.rationale}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-1.5 text-[11px] text-zinc-500">
                      <span>{plan.dishes.length} dishes</span>
                      <span>•</span>
                      <span>
                        {missingIngredients.length === 0
                          ? "No shopping"
                          : `${missingIngredients.length} items to buy`}
                      </span>
                      <span>•</span>
                      <span>
                        {hasViolations ? "Needs fixes" : "Ready to approve"}
                      </span>
                    </div>
                  </div>
                </TabsTrigger>
              );
            })}
          </TabsList>

          {plans.map((plan) => {
            const missingIngredients = getMissingIngredients(plan);
            const hasViolations = plan.validation && !plan.validation.is_valid;

            return (
              <TabsContent key={plan.id} value={`plan-${plan.id}`}>
                <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
                  <Card className="p-5">
                    <div className="flex items-start justify-between gap-3">
                      <Badge
                        className={
                          CUISINE_COLORS[plan.template_id] ||
                          "bg-zinc-100 text-zinc-800"
                        }
                      >
                        {CUISINE_LABELS[plan.template_id] || plan.cuisine}
                      </Badge>
                      <span className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-muted-foreground">
                        {plan.dishes.length} dishes
                      </span>
                    </div>

                    <p className="mt-4 text-sm leading-6 text-zinc-600">
                      {plan.rationale}
                    </p>

                    <div className="mt-5 space-y-2">
                      {plan.dishes.map((dish) => (
                        <button
                          key={dish.recipe_id}
                          type="button"
                          className="group flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition-colors hover:bg-zinc-50"
                          onClick={() => handleOpenSwap(plan.id, dish)}
                          aria-label={`Swap ${dish.name}`}
                        >
                          <span>{ROLE_EMOJI[dish.role] || "🍽️"}</span>
                          <span className="flex-1 font-medium text-zinc-900">
                            {dish.name}
                          </span>
                          <ArrowLeftRight className="h-3.5 w-3.5 text-zinc-300 transition-colors group-hover:text-zinc-500" />
                          <Badge variant="outline" className="text-[10px]">
                            {ROLE_LABELS[dish.role] || dish.role}
                          </Badge>
                        </button>
                      ))}
                    </div>

                    <Separator className="my-4" />

                    <div className="grid grid-cols-2 gap-2 text-xs text-zinc-600">
                      <div>🥚 Eggs: {plan.egg_style}</div>
                      <div>🫓 Roti: {plan.roti_count}</div>
                    </div>

                    <button
                      type="button"
                      className={`mt-4 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-xs transition-colors ${
                        plan.include_curd_rice_side
                          ? "border border-blue-200 bg-blue-50 text-blue-700"
                          : "bg-zinc-50 text-zinc-500 hover:bg-zinc-100"
                      }`}
                      onClick={() =>
                        handleToggleCurdRice(
                          plan.id,
                          plan.include_curd_rice_side
                        )
                      }
                      disabled={togglingCurdRice}
                      aria-label="Toggle optional curd rice side"
                    >
                      <span>🍚</span>
                      <span className="flex-1">Optional curd rice side</span>
                      <span
                        className={`inline-flex h-5 w-9 items-center justify-center rounded-full transition-colors ${
                          plan.include_curd_rice_side
                            ? "bg-blue-600"
                            : "bg-zinc-300"
                        }`}
                      >
                        <span
                          className={`block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
                            plan.include_curd_rice_side
                              ? "translate-x-2"
                              : "-translate-x-2"
                          }`}
                        />
                      </span>
                    </button>

                    {plan.kid_notes && (
                      <div className="mt-4 flex items-start gap-2 rounded-xl bg-blue-50 p-3">
                        <Baby className="mt-0.5 h-3.5 w-3.5 shrink-0 text-blue-500" />
                        <span className="text-xs leading-5 text-blue-700">
                          {plan.kid_notes}
                        </span>
                      </div>
                    )}
                  </Card>

                  <Card className="h-fit p-5">
                    <div className="space-y-3">
                      <PlanSnapshotRow
                        label="Cuisine"
                        value={CUISINE_LABELS[plan.template_id] || plan.cuisine}
                      />
                      <PlanSnapshotRow
                        label="Shopping"
                        value={
                          missingIngredients.length === 0
                            ? "No shopping needed"
                            : `${missingIngredients.length} missing items`
                        }
                      />
                      <PlanSnapshotRow
                        label="Approval"
                        value={
                          hasViolations
                            ? "Blocked by rule violations"
                            : "Ready to approve"
                        }
                      />
                    </div>

                    {missingIngredients.length > 0 && (
                      <div className="mt-4 rounded-xl bg-amber-50 p-3">
                        <div className="mb-2 flex items-center gap-1 text-xs font-medium text-amber-700">
                          <AlertTriangle className="h-3 w-3" />
                          Needs shopping
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {missingIngredients.map((item) => (
                            <Badge
                              key={item}
                              variant="outline"
                              className="border-amber-200 text-xs text-amber-700"
                            >
                              {item}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {hasViolations && (
                      <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3">
                        <div className="mb-2 flex items-center gap-1 text-xs font-medium text-red-700">
                          <AlertTriangle className="h-3 w-3" />
                          Rule violations
                        </div>
                        <ul className="space-y-0.5 text-xs text-red-600">
                          {plan.validation!.violations.map((v, i) => (
                            <li key={i}>• {v}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <Button
                      className="mt-5 h-12 w-full rounded-xl gap-2"
                      onClick={() => handleApprove(plan.id)}
                      disabled={approving !== null || !!hasViolations}
                    >
                      {approving === plan.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                      {hasViolations
                        ? "Cannot Approve (Rule Violations)"
                        : "Approve This Plan"}
                    </Button>
                  </Card>
                </div>
              </TabsContent>
            );
          })}
        </Tabs>

        {/* Swap Dish Sheet */}
        <Sheet open={swapSheetOpen} onOpenChange={setSwapSheetOpen}>
          <SheetContent side="bottom" className="max-h-[70vh]">
            <SheetHeader>
              <SheetTitle>
                Swap {swapTarget?.dish.name ?? "Dish"}
              </SheetTitle>
              <SheetDescription>
                Choose an alternative for{" "}
                {ROLE_LABELS[swapTarget?.dish.role ?? ""] ||
                  swapTarget?.dish.role}
              </SheetDescription>
            </SheetHeader>

            <ScrollArea className="flex-1 px-4 pb-4">
              {loadingSwapOptions ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
                </div>
              ) : swapOptions.length === 0 ? (
                <div className="text-center py-8 text-sm text-zinc-400">
                  No alternatives available for this role.
                </div>
              ) : (
                <div className="space-y-2">
                  {swapOptions.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      className="w-full text-left p-3 rounded-xl border border-zinc-200 hover:border-zinc-400 hover:bg-zinc-50 transition-colors disabled:opacity-50"
                      onClick={() => handleSelectSwap(option)}
                      disabled={swapping}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-zinc-900 text-sm">
                          {option.name}
                        </span>
                        <ArrowLeftRight className="h-3.5 w-3.5 text-zinc-400" />
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {option.cuisine_tags.map((tag) => (
                          <Badge
                            key={tag}
                            variant="outline"
                            className={`text-[10px] ${
                              CUISINE_COLORS[tag] || "bg-zinc-100 text-zinc-600"
                            }`}
                          >
                            {CUISINE_LABELS[tag] || tag}
                          </Badge>
                        ))}
                        <Badge
                          variant="outline"
                          className="text-[10px]"
                        >
                          {PROTEIN_LABELS[option.protein_tier] ||
                            option.protein_tier}
                        </Badge>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </ScrollArea>
          </SheetContent>
        </Sheet>
      </div>
      <NavBar />
    </div>
  );
}

function PlanSummary({ plan }: { plan: MealPlanResponse }) {
  return (
    <div className="space-y-2">
      {/* Dishes */}
      {plan.dishes.map((dish) => (
        <div
          key={dish.recipe_id}
          className="flex items-center gap-2 text-sm"
        >
          <span>{ROLE_EMOJI[dish.role] || "🍽️"}</span>
          <span className="font-medium text-zinc-900">{dish.name}</span>
          <Badge variant="outline" className="text-[10px] ml-auto">
            {ROLE_LABELS[dish.role] || dish.role}
          </Badge>
        </div>
      ))}

      <Separator className="my-2" />

      {/* Constants */}
      <div className="grid grid-cols-2 gap-2 text-xs text-zinc-600">
        <div>🥚 Eggs: {plan.egg_style}</div>
        <div>🫓 Roti: {plan.roti_count}</div>
        {plan.include_curd_rice_side && (
          <div>🍚 Optional curd rice side</div>
        )}
      </div>

      {/* Kid notes */}
      {plan.kid_notes && (
        <div className="flex items-start gap-1.5 mt-2 p-2 bg-blue-50 rounded-lg">
          <Baby className="h-3.5 w-3.5 text-blue-500 mt-0.5 shrink-0" />
          <span className="text-xs text-blue-700">{plan.kid_notes}</span>
        </div>
      )}
    </div>
  );
}

function PlanSnapshotRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-[rgba(244,244,239,0.74)] px-3 py-2.5">
      <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-sm font-medium text-zinc-900">{value}</div>
    </div>
  );
}
