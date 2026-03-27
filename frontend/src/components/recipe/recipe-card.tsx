"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Clock, Flame } from "lucide-react";
import {
  type RecipeListItem,
  CUISINE_LABELS,
  CUISINE_COLORS,
  PROTEIN_COLORS,
  PROTEIN_LABELS,
} from "@/types";

interface RecipeCardProps {
  recipe: RecipeListItem;
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  const totalTime =
    (recipe.prep_time_minutes ?? 0) + (recipe.cook_time_minutes ?? 0);

  return (
    <Link href={`/recipes/${recipe.id}`}>
      <div className="bg-white border border-zinc-200 rounded-xl p-4 hover:border-zinc-300 hover:shadow-sm transition-all active:scale-[0.98]">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-zinc-900 truncate">{recipe.name}</h3>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {recipe.cuisine_tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className={`text-[10px] font-medium ${CUISINE_COLORS[tag] ?? "bg-zinc-100 text-zinc-600"}`}
                >
                  {CUISINE_LABELS[tag] ?? tag}
                </Badge>
              ))}
              <Badge
                variant="secondary"
                className={`text-[10px] font-medium ${PROTEIN_COLORS[recipe.protein_tier]}`}
              >
                <Flame className="h-2.5 w-2.5 mr-0.5" />
                {PROTEIN_LABELS[recipe.protein_tier]}
              </Badge>
              {recipe.is_side_dish && (
                <Badge variant="outline" className="text-[10px] font-medium">
                  Side Dish
                </Badge>
              )}
            </div>
          </div>
          {totalTime > 0 && (
            <div className="flex items-center gap-1 text-xs text-zinc-400 flex-shrink-0">
              <Clock className="h-3 w-3" />
              <span>{totalTime}m</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
