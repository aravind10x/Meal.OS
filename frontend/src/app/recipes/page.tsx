"use client";

import { useEffect, useState } from "react";
import { NavBar } from "@/components/common/nav-bar";
import { PageHeader } from "@/components/common/page-header";
import { RecipeCard } from "@/components/recipe/recipe-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { api } from "@/lib/api";
import { type RecipeListItem, CUISINE_LABELS, CUISINE_COLORS } from "@/types";
import Link from "next/link";
import { cn } from "@/lib/utils";

const FILTER_OPTIONS = [
  { value: "all", label: "All" },
  { value: "south_indian", label: "South Indian" },
  { value: "north_indian", label: "North Indian" },
  { value: "indo_chinese", label: "Indo-Chinese" },
  { value: "bengali", label: "Bengali" },
  { value: "comfort", label: "Comfort" },
];

export default function RecipesPage() {
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [showSidesOnly, setShowSidesOnly] = useState<boolean | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await api.recipes.list(
          filter !== "all" ? { cuisine: filter } : undefined
        );
        setRecipes(data);
      } catch (err) {
        console.error("Failed to load recipes:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filter]);

  const filtered =
    showSidesOnly === null
      ? recipes
      : recipes.filter((r) => r.is_side_dish === showSidesOnly);

  const mainDishes = filtered.filter((r) => !r.is_side_dish);
  const sideDishes = filtered.filter((r) => r.is_side_dish);

  return (
    <div className="min-h-screen pb-20">
      <div className="mx-auto max-w-lg px-4 pt-6">
        <PageHeader
          title="Recipes"
          subtitle={`${recipes.length} house-style recipes`}
          action={
            <Link href="/recipes/new">
              <Button size="sm" className="rounded-full">
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            </Link>
          }
        />

        {/* Cuisine filter */}
        <div className="flex gap-2 overflow-x-auto pb-2 mb-2 scrollbar-hide">
          {FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFilter(opt.value)}
              className={cn(
                "px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors border",
                filter === opt.value
                  ? "bg-zinc-900 text-white border-zinc-900"
                  : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-300"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Type toggle */}
        <div className="flex gap-2 mb-4">
          {[
            { value: null, label: "All" },
            { value: false, label: "Main Dishes" },
            { value: true, label: "Side Dishes" },
          ].map((opt) => (
            <button
              key={String(opt.value)}
              onClick={() => setShowSidesOnly(opt.value)}
              className={cn(
                "px-3 py-1 rounded-full text-xs font-medium transition-colors border",
                showSidesOnly === opt.value
                  ? "bg-zinc-800 text-white border-zinc-800"
                  : "bg-white text-zinc-500 border-zinc-200 hover:border-zinc-300"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white border border-zinc-200 rounded-xl p-4 animate-pulse"
              >
                <div className="h-4 bg-zinc-200 rounded w-2/3 mb-3" />
                <div className="flex gap-2">
                  <div className="h-5 bg-zinc-100 rounded-full w-20" />
                  <div className="h-5 bg-zinc-100 rounded-full w-16" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Main dishes */}
            {mainDishes.length > 0 && (showSidesOnly === null || !showSidesOnly) && (
              <div>
                {showSidesOnly === null && (
                  <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider mb-3">
                    Main Dishes ({mainDishes.length})
                  </h2>
                )}
                <div className="space-y-2">
                  {mainDishes.map((recipe) => (
                    <RecipeCard key={recipe.id} recipe={recipe} />
                  ))}
                </div>
              </div>
            )}

            {/* Side dishes */}
            {sideDishes.length > 0 && (showSidesOnly === null || showSidesOnly) && (
              <div>
                {showSidesOnly === null && (
                  <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider mb-3">
                    Side Dishes ({sideDishes.length})
                  </h2>
                )}
                <div className="space-y-2">
                  {sideDishes.map((recipe) => (
                    <RecipeCard key={recipe.id} recipe={recipe} />
                  ))}
                </div>
              </div>
            )}

            {filtered.length === 0 && (
              <div className="text-center py-12 text-zinc-400">
                <p>No recipes found.</p>
              </div>
            )}
          </div>
        )}
      </div>

      <NavBar />
    </div>
  );
}
