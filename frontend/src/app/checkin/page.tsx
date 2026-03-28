"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { NavBar } from "@/components/common/nav-bar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
  CalendarDays,
  Loader2,
  Plus,
  Trash2,
  Sparkles,
  Check,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import { getTomorrowDate } from "@/lib/utils";
import type {
  LeftoverItem,
  ServingsEstimate,
  VegetableCategory,
} from "@/types";

const SERVINGS_OPTIONS: { value: ServingsEstimate; label: string }[] = [
  { value: "small", label: "Small" },
  { value: "1_serving", label: "1 serving" },
  { value: "2_plus_servings", label: "2+ servings" },
];

function formatDate(dateStr: string): string {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-IN", {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
}

export default function CheckinPage() {
  const router = useRouter();
  const tomorrow = getTomorrowDate();

  // State
  const [leftovers, setLeftovers] = useState<LeftoverItem[]>([]);
  const [selectedVegs, setSelectedVegs] = useState<string[]>([]);
  const [useSoonVegs, setUseSoonVegs] = useState<string[]>([]);
  const [vegCategories, setVegCategories] = useState<VegetableCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loadingVegs, setLoadingVegs] = useState(true);

  // Previous check-in data for "Same as yesterday" shortcut
  const [previousVegs, setPreviousVegs] = useState<string[]>([]);
  const [previousUseSoon, setPreviousUseSoon] = useState<string[]>([]);
  const [hasPreviousCheckin, setHasPreviousCheckin] = useState(false);

  // Load vegetable reference data
  useEffect(() => {
    api.vegetables
      .list()
      .then((data) => setVegCategories(data.vegetables))
      .catch(() => toast.error("Failed to load vegetables"))
      .finally(() => setLoadingVegs(false));
  }, []);

  // Load latest check-in (prefill or store for "same as yesterday")
  useEffect(() => {
    api.checkin
      .latest()
      .then((data) => {
        // Always store previous vegetables for "Same as yesterday"
        if (data.vegetables.length > 0) {
          setPreviousVegs(data.vegetables);
          setPreviousUseSoon(data.use_soon);
          setHasPreviousCheckin(true);
        }

        if (data.plan_date === tomorrow) {
          // Restore leftover state from active leftovers
          setLeftovers(
            data.active_leftovers.map((lo) => ({
              dish_name: lo.dish_name,
              recipe_id: lo.recipe_id,
              servings_estimate: lo.servings_estimate as ServingsEstimate,
              notes: lo.notes,
            }))
          );
          setSelectedVegs(data.vegetables);
          setUseSoonVegs(data.use_soon);
          setSubmitted(true);
        }
      })
      .catch(() => {
        // No previous check-in — that's fine
      });
  }, [tomorrow]);

  // "Same as yesterday" shortcut
  const handleSameAsYesterday = useCallback(() => {
    setSelectedVegs(previousVegs);
    setUseSoonVegs(previousUseSoon);
    toast.success("Vegetables carried over from last check-in");
  }, [previousVegs, previousUseSoon]);

  // "No leftovers" shortcut
  const handleNoLeftovers = useCallback(() => {
    setLeftovers([]);
    toast.success("Leftovers cleared");
  }, []);

  // Leftover management
  const addLeftover = () => {
    setLeftovers((prev) => [
      ...prev,
      { dish_name: "", servings_estimate: "small", notes: "" },
    ]);
  };

  const updateLeftover = (
    index: number,
    field: keyof LeftoverItem,
    value: string
  ) => {
    setLeftovers((prev) =>
      prev.map((lo, i) => (i === index ? { ...lo, [field]: value } : lo))
    );
  };

  const removeLeftover = (index: number) => {
    setLeftovers((prev) => prev.filter((_, i) => i !== index));
  };

  // Vegetable selection
  const toggleVeg = useCallback((name: string) => {
    setSelectedVegs((prev) => {
      const isSelected = prev.includes(name);
      if (isSelected) {
        setUseSoonVegs((useSoonPrev) =>
          useSoonPrev.filter((veg) => veg !== name)
        );
        return prev.filter((veg) => veg !== name);
      }
      return [...prev, name];
    });
  }, []);

  const toggleUseSoon = useCallback((name: string) => {
    setUseSoonVegs((prev) =>
      prev.includes(name) ? prev.filter((v) => v !== name) : [...prev, name]
    );
  }, []);

  // Submit check-in
  const handleSubmit = async () => {
    setLoading(true);
    try {
      await api.checkin.submit({
        plan_date: tomorrow,
        leftovers: leftovers.filter((lo) => lo.dish_name.trim()),
        vegetables: selectedVegs,
        use_soon: useSoonVegs.filter((v) => selectedVegs.includes(v)),
      });
      toast.success("Check-in saved!");
      setSubmitted(true);
    } catch {
      toast.error("Failed to save check-in");
    } finally {
      setLoading(false);
    }
  };

  // Generate plans
  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const plans = await api.planner.generate({
        plan_date: tomorrow,
        vegetables: selectedVegs,
        use_soon: useSoonVegs.filter((v) => selectedVegs.includes(v)),
        leftovers: leftovers
          .filter((lo) => lo.dish_name.trim())
          .map((lo) => ({
            dish_name: lo.dish_name,
            servings_estimate: lo.servings_estimate,
          })),
      });
      toast.success(`${plans.length} meal plans generated!`);
      router.push(`/plans?date=${tomorrow}`);
    } catch (error) {
      toast.error(
        error instanceof Error && error.message
          ? error.message
          : "Failed to generate plans. Please try again."
      );
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen pb-20">
      <div className="mx-auto max-w-lg px-4 pt-6">
        <PageHeader
          title="Check-in"
          subtitle={formatDate(tomorrow)}
        />

        {/* Step 1: Leftovers */}
        <section className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-zinc-900">Leftovers</h2>
            <div className="flex gap-1.5">
              {leftovers.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNoLeftovers}
                  className="text-xs text-zinc-500"
                >
                  Clear
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={addLeftover}
                className="gap-1"
              >
                <Plus className="h-3.5 w-3.5" /> Add
              </Button>
            </div>
          </div>

          {leftovers.length === 0 ? (
            <Card className="p-4 text-center text-sm text-zinc-400">
              No leftovers added.
            </Card>
          ) : (
            <div className="space-y-3">
              {leftovers.map((lo, i) => (
                <Card key={i} className="p-3">
                  <div className="flex items-start gap-2">
                    <div className="flex-1 space-y-2">
                      <Input
                        placeholder="Dish name (e.g., Yesterday's Dal)"
                        value={lo.dish_name}
                        onChange={(e) =>
                          updateLeftover(i, "dish_name", e.target.value)
                        }
                      />
                      <div className="flex flex-wrap gap-1.5">
                        {SERVINGS_OPTIONS.map((opt) => (
                          <Badge
                            key={opt.value}
                            variant={
                              lo.servings_estimate === opt.value
                                ? "default"
                                : "outline"
                            }
                            className="cursor-pointer"
                            onClick={() =>
                              updateLeftover(
                                i,
                                "servings_estimate",
                                opt.value
                              )
                            }
                          >
                            {opt.label}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-zinc-400 hover:text-red-500 shrink-0"
                      onClick={() => removeLeftover(i)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </section>

        <Separator className="mb-6" />

        {/* Step 2: Vegetable selection */}
        <section className="mb-6">
          <div className="flex items-center justify-between mb-1">
            <h2 className="font-semibold text-zinc-900">Vegetables</h2>
            {hasPreviousCheckin && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleSameAsYesterday}
                className="text-xs gap-1"
              >
                <Check className="h-3 w-3" />
                Use last check-in
              </Button>
            )}
          </div>
          <p className="text-xs text-zinc-500 mb-3 leading-5">
            Tap to include. Tap again for &quot;use soon&quot;. Tap again to
            clear.
          </p>

          {loadingVegs ? (
            <div className="flex items-center justify-center p-6">
              <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
            </div>
          ) : (
            <div className="space-y-4">
              {vegCategories.map((cat) => (
                <div key={cat.category}>
                  <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">
                    {cat.category}
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {cat.items.map((veg) => {
                      const isSelected = selectedVegs.includes(veg.name);
                      const isUseSoon = useSoonVegs.includes(veg.name);
                      return (
                        <Badge
                          key={veg.name}
                          variant={isSelected ? "default" : "outline"}
                          className={`cursor-pointer transition-all ${
                            isUseSoon
                              ? "ring-2 ring-amber-400 bg-amber-50 text-amber-800 border-amber-200"
                              : isSelected
                              ? ""
                              : "hover:bg-zinc-100"
                          }`}
                          onClick={() => {
                            if (!isSelected) {
                              toggleVeg(veg.name);
                            } else if (!isUseSoon) {
                              toggleUseSoon(veg.name);
                            } else {
                              // Third tap: deselect everything
                              setUseSoonVegs((prev) =>
                                prev.filter((v) => v !== veg.name)
                              );
                              toggleVeg(veg.name);
                            }
                          }}
                        >
                          {isUseSoon && (
                            <AlertTriangle className="h-3 w-3 mr-1" />
                          )}
                          {isSelected && !isUseSoon && (
                            <Check className="h-3 w-3 mr-1" />
                          )}
                          {veg.name}
                          {veg.seasonal && (
                            <span className="ml-1 text-[10px]">🌿</span>
                          )}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedVegs.length > 0 && (
            <div className="mt-3 text-xs text-zinc-500">
              {selectedVegs.length} vegetables selected
              {useSoonVegs.length > 0 && (
                <span className="text-amber-600 ml-1">
                  ({useSoonVegs.length} use soon)
                </span>
              )}
            </div>
          )}
        </section>

        <Separator className="mb-6" />

        {/* Actions */}
        <div className="space-y-3">
          {!submitted ? (
            <Button
              className="w-full rounded-xl h-12"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <CalendarDays className="h-4 w-4 mr-2" />
              )}
              Save Check-in
            </Button>
          ) : (
            <>
              <Card className="p-3 bg-emerald-50 border-emerald-200">
                <div className="flex items-center gap-2 text-emerald-700 text-sm">
                  <Check className="h-4 w-4" />
                  Saved for {formatDate(tomorrow)}
                </div>
              </Card>
              <Button
                className="w-full rounded-xl h-12 gap-2"
                onClick={handleGenerate}
                disabled={generating}
              >
                {generating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                Generate Plans
              </Button>
              <Button
                variant="outline"
                className="w-full rounded-xl"
                onClick={() => setSubmitted(false)}
              >
                Edit Check-in
              </Button>
            </>
          )}
        </div>
      </div>

      <NavBar />
    </div>
  );
}
