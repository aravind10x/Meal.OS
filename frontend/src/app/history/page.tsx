"use client";

import { useEffect, useState } from "react";
import { NavBar } from "@/components/common/nav-bar";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Loader2, ClipboardList } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { MealHistoryResponse } from "@/types";
import { CUISINE_LABELS, CUISINE_COLORS } from "@/types";

export default function HistoryPage() {
  const [history, setHistory] = useState<MealHistoryResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.planner
      .history(14)
      .then(setHistory)
      .catch(() => toast.error("Failed to load history"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen pb-20">
      <div className="mx-auto max-w-lg px-4 pt-6">
        <PageHeader title="Meal History" subtitle="Last 14 days" />

        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
          </div>
        ) : history.length === 0 ? (
          <Card className="p-8 text-center">
            <ClipboardList className="h-10 w-10 text-zinc-300 mx-auto mb-3" />
            <h3 className="font-semibold text-zinc-600 mb-1">No history yet</h3>
            <p className="text-sm text-zinc-400">
              Meal history will appear here after you approve your first plan.
            </p>
          </Card>
        ) : (
          <div className="space-y-2">
            {history.map((h) => (
              <Card key={h.history_date} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="text-sm font-medium text-zinc-900">
                    {new Date(h.history_date + "T00:00:00").toLocaleDateString(
                      "en-IN",
                      { weekday: "long", month: "short", day: "numeric" }
                    )}
                  </div>
                  <Badge
                    className={
                      CUISINE_COLORS[h.cuisine.toLowerCase().replace(/ /g, "_")] ||
                      "bg-zinc-100 text-zinc-800"
                    }
                  >
                    {h.cuisine}
                  </Badge>
                </div>
                <div className="space-y-1">
                  {h.dishes_cooked.map((dish) => (
                    <div key={dish} className="text-sm text-zinc-600">
                      • {dish.replace(/_/g, " ")}
                    </div>
                  ))}
                </div>
                <div className="mt-2 text-xs text-zinc-400">
                  Eggs: {h.egg_style}
                  {h.notes && ` · ${h.notes}`}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
      <NavBar />
    </div>
  );
}
