"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { NavBar } from "@/components/common/nav-bar";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
  ArrowLeft,
  Loader2,
  ShoppingCart,
  Check,
  Copy,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { ShoppingItem } from "@/types";

const CATEGORY_CONFIG: Record<
  string,
  { label: string; color: string; icon: string }
> = {
  needed: {
    label: "Need to Buy",
    color: "bg-red-50 border-red-200",
    icon: "🛒",
  },
  likely_available: {
    label: "Likely Available",
    color: "bg-amber-50 border-amber-200",
    icon: "✅",
  },
  pantry_staple: {
    label: "Pantry Staples",
    color: "bg-zinc-50 border-zinc-200",
    icon: "🫙",
  },
};

export default function ShoppingListPage() {
  const params = useParams();
  const router = useRouter();
  const planId = Number(params.id);

  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!planId) return;
    api.shopping
      .get(planId)
      .then((data) => setItems(data.items))
      .catch(() => toast.error("Failed to load shopping list"))
      .finally(() => setLoading(false));
  }, [planId]);

  const neededItems = items.filter((i) => i.category === "needed");
  const availableItems = items.filter((i) => i.category === "likely_available");
  const pantryItems = items.filter((i) => i.category === "pantry_staple");

  const handleCopy = async () => {
    const text = neededItems
      .map((item) => `☐ ${item.name} — ${item.quantity} (${item.for_dish})`)
      .join("\n");
    try {
      await navigator.clipboard.writeText(
        `🛒 Shopping List\n\n${text}`
      );
      setCopied(true);
      toast.success("Shopping list copied!");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy");
    }
  };

  return (
    <div className="min-h-screen pb-20">
      <div className="mx-auto max-w-lg px-4 pt-6">
        <PageHeader
          title="Shopping List"
          subtitle={`${neededItems.length} items to buy`}
          action={
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
          }
        />

        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
          </div>
        ) : items.length === 0 ? (
          <Card className="p-8 text-center">
            <ShoppingCart className="h-10 w-10 text-zinc-300 mx-auto mb-3" />
            <h3 className="font-semibold text-zinc-600 mb-1">
              No shopping needed!
            </h3>
            <p className="text-sm text-zinc-400">
              Everything is available at home.
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {/* Need to Buy */}
            {neededItems.length > 0 && (
              <ShoppingCategory
                title={CATEGORY_CONFIG.needed.label}
                icon={CATEGORY_CONFIG.needed.icon}
                items={neededItems}
                cardClass={CATEGORY_CONFIG.needed.color}
              />
            )}

            {/* Likely Available */}
            {availableItems.length > 0 && (
              <ShoppingCategory
                title={CATEGORY_CONFIG.likely_available.label}
                icon={CATEGORY_CONFIG.likely_available.icon}
                items={availableItems}
                cardClass={CATEGORY_CONFIG.likely_available.color}
              />
            )}

            {/* Pantry Staples */}
            {pantryItems.length > 0 && (
              <ShoppingCategory
                title={CATEGORY_CONFIG.pantry_staple.label}
                icon={CATEGORY_CONFIG.pantry_staple.icon}
                items={pantryItems}
                cardClass={CATEGORY_CONFIG.pantry_staple.color}
              />
            )}

            <Separator />

            {neededItems.length > 0 && (
              <Button
                variant="outline"
                className="w-full rounded-xl gap-2"
                onClick={handleCopy}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
                {copied ? "Copied!" : "Copy Shopping List"}
              </Button>
            )}
          </div>
        )}
      </div>
      <NavBar />
    </div>
  );
}

function ShoppingCategory({
  title,
  icon,
  items,
  cardClass,
}: {
  title: string;
  icon: string;
  items: ShoppingItem[];
  cardClass: string;
}) {
  return (
    <div>
      <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">
        {icon} {title} ({items.length})
      </h3>
      <Card className={`divide-y divide-zinc-100 ${cardClass}`}>
        {items.map((item, i) => (
          <div key={`${item.name}-${i}`} className="px-4 py-2.5 flex items-center gap-3">
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm text-zinc-900">
                {item.name}
              </div>
              <div className="text-xs text-zinc-500">
                {item.quantity} · for {item.for_dish}
              </div>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}
