"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { NavBar } from "@/components/common/nav-bar";
import { RecipeForm } from "@/components/recipe/recipe-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  ArrowLeft,
  Clock,
  Flame,
  Baby,
  AlertTriangle,
  Users,
  ChefHat,
  Pencil,
  Trash2,
  ExternalLink,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  type Recipe,
  type RecipeCreate,
  CUISINE_LABELS,
  CUISINE_COLORS,
  PROTEIN_COLORS,
  PROTEIN_LABELS,
  FAMILIARITY_LABELS,
} from "@/types";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export default function RecipeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);

  const recipeId = params.id as string;

  useEffect(() => {
    async function load() {
      try {
        const data = await api.recipes.get(recipeId);
        setRecipe(data);
      } catch {
        toast.error("Recipe not found");
        router.push("/recipes");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [recipeId, router]);

  const handleDelete = async () => {
    if (!confirm("Delete this recipe? This cannot be undone.")) return;
    try {
      await api.recipes.delete(recipeId);
      toast.success("Recipe deleted");
      router.push("/recipes");
    } catch {
      toast.error("Failed to delete recipe");
    }
  };

  const toggleFamiliarity = async () => {
    if (!recipe) return;
    const cycle: Record<string, string> = {
      new: "needs_instructions",
      needs_instructions: "known",
      known: "new",
    };
    const next = cycle[recipe.cook_familiarity] || "needs_instructions";
    try {
      const updated = await api.recipes.update(recipeId, {
        cook_familiarity: next as "known" | "needs_instructions" | "new",
      });
      setRecipe(updated);
      toast.success(`Updated to: ${FAMILIARITY_LABELS[next]}`);
    } catch {
      toast.error("Failed to update");
    }
  };

  const handleEdit = async (data: RecipeCreate) => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { id, ...updateData } = data;
      const updated = await api.recipes.update(recipeId, updateData);
      setRecipe(updated);
      setEditing(false);
      toast.success("Recipe updated!");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to update recipe";
      toast.error(message);
      throw err;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pb-20">
        <div className="mx-auto max-w-lg px-4 pt-6 animate-pulse">
          <div className="h-6 bg-zinc-200 rounded w-1/3 mb-4" />
          <div className="h-8 bg-zinc-200 rounded w-2/3 mb-2" />
          <div className="h-4 bg-zinc-100 rounded w-full mb-6" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-zinc-100 rounded-xl" />
            ))}
          </div>
        </div>
        <NavBar />
      </div>
    );
  }

  if (!recipe) return null;

  // --- Edit mode ---
  if (editing) {
    return (
      <div className="min-h-screen pb-20">
        <div className="mx-auto max-w-lg px-4 pt-4">
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => setEditing(false)}
              className="flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-900 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to detail
            </button>
          </div>
          <h1 className="text-xl font-bold text-zinc-900 mb-4">
            Edit: {recipe.name}
          </h1>
          <RecipeForm
            initialData={{
              id: recipe.id,
              name: recipe.name,
              description: recipe.description,
              cuisine_tags: recipe.cuisine_tags,
              meal_template: recipe.meal_template,
              is_side_dish: recipe.is_side_dish,
              ingredients: recipe.ingredients,
              steps: recipe.steps,
              critical_notes: recipe.critical_notes,
              kid_adaptation: recipe.kid_adaptation,
              preferred_side_pairings: recipe.preferred_side_pairings,
              protein_tier: recipe.protein_tier,
              cook_familiarity: recipe.cook_familiarity,
              links: recipe.links,
              serves: recipe.serves,
              prep_time_minutes: recipe.prep_time_minutes,
              cook_time_minutes: recipe.cook_time_minutes,
            }}
            isNew={false}
            onSubmit={handleEdit}
            onCancel={() => setEditing(false)}
            submitLabel="Save Changes"
          />
        </div>
        <NavBar />
      </div>
    );
  }

  // --- View mode ---
  const totalTime =
    (recipe.prep_time_minutes ?? 0) + (recipe.cook_time_minutes ?? 0);
  const vegIngredients = recipe.ingredients.filter(
    (i) => i.category === "vegetable"
  );
  const pantryIngredients = recipe.ingredients.filter(
    (i) => i.category === "pantry"
  );

  return (
    <div className="min-h-screen pb-20">
      <div className="mx-auto max-w-lg px-4 pt-4">
        {/* Back button + actions */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => router.push("/recipes")}
            className="flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-900 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Recipes
          </button>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="rounded-full"
              onClick={() => setEditing(true)}
            >
              <Pencil className="h-3.5 w-3.5 mr-1" />
              Edit
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="rounded-full"
              onClick={handleDelete}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Title + tags */}
        <h1 className="text-2xl font-bold text-zinc-900 mb-2">{recipe.name}</h1>
        {recipe.description && (
          <p className="text-sm text-zinc-500 mb-3">{recipe.description}</p>
        )}

        <div className="flex flex-wrap gap-1.5 mb-4">
          {recipe.cuisine_tags.map((tag) => (
            <Badge
              key={tag}
              variant="secondary"
              className={`text-xs ${CUISINE_COLORS[tag] ?? ""}`}
            >
              {CUISINE_LABELS[tag] ?? tag}
            </Badge>
          ))}
          <Badge
            variant="secondary"
            className={`text-xs ${PROTEIN_COLORS[recipe.protein_tier]}`}
          >
            <Flame className="h-3 w-3 mr-0.5" />
            {PROTEIN_LABELS[recipe.protein_tier]}
          </Badge>
        </div>

        {/* Meta bar */}
        <div className="flex items-center gap-4 text-xs text-zinc-500 mb-5">
          {totalTime > 0 && (
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {recipe.prep_time_minutes ?? 0}m prep + {recipe.cook_time_minutes ?? 0}m cook
            </span>
          )}
          <span className="flex items-center gap-1">
            <Users className="h-3.5 w-3.5" />
            Serves {recipe.serves}
          </span>
        </div>

        {/* Cook familiarity toggle */}
        <button
          onClick={toggleFamiliarity}
          className={cn(
            "w-full rounded-xl p-3 mb-5 text-left transition-colors border",
            recipe.cook_familiarity === "known"
              ? "bg-emerald-50 border-emerald-200"
              : recipe.cook_familiarity === "new"
                ? "bg-amber-50 border-amber-200"
                : "bg-blue-50 border-blue-200"
          )}
        >
          <div className="flex items-center gap-2">
            <ChefHat className="h-4 w-4" />
            <span className="text-sm font-medium">
              {FAMILIARITY_LABELS[recipe.cook_familiarity]}
            </span>
            <span className="text-xs text-zinc-400 ml-auto">Tap to change</span>
          </div>
        </button>

        {/* Critical Notes */}
        {recipe.critical_notes && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-5">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-amber-800 mb-1">
                  Critical Notes
                </h3>
                <p className="text-sm text-amber-700">{recipe.critical_notes}</p>
              </div>
            </div>
          </div>
        )}

        {/* Kid Adaptation */}
        {recipe.kid_adaptation && (
          <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 mb-5">
            <div className="flex items-start gap-2">
              <Baby className="h-4 w-4 text-sky-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-sky-800 mb-1">
                  Kid Adaptation
                </h3>
                <p className="text-sm text-sky-700">{recipe.kid_adaptation}</p>
              </div>
            </div>
          </div>
        )}

        <Separator className="mb-5" />

        {/* Ingredients */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-zinc-900 mb-3">Ingredients</h2>

          {vegIngredients.length > 0 && (
            <div className="mb-3">
              <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">
                Vegetables
              </h3>
              <ul className="space-y-1.5">
                {vegIngredients.map((ing, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-zinc-700"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                    <div>
                      <span className="font-medium">{ing.name}</span>
                      {ing.quantity && (
                        <span className="text-zinc-500"> — {ing.quantity}</span>
                      )}
                      {ing.note && (
                        <span className="text-zinc-400 text-xs block">
                          {ing.note}
                        </span>
                      )}
                      {ing.flexible_with && ing.flexible_with.length > 0 && (
                        <span className="text-xs text-zinc-400 block">
                          Can substitute: {ing.flexible_with.join(", ")}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {pantryIngredients.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">
                Pantry
              </h3>
              <ul className="space-y-1.5">
                {pantryIngredients.map((ing, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-zinc-600"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-300 mt-1.5 flex-shrink-0" />
                    <div>
                      <span>{ing.name}</span>
                      {ing.quantity && (
                        <span className="text-zinc-400"> — {ing.quantity}</span>
                      )}
                      {ing.note && (
                        <span className="text-zinc-400 text-xs block">
                          {ing.note}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <Separator className="mb-5" />

        {/* Steps */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-zinc-900 mb-3">Steps</h2>
          <ol className="space-y-4">
            {recipe.steps.map((step) => (
              <li key={step.order} className="flex gap-3">
                <span
                  className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5",
                    step.is_critical
                      ? "bg-amber-100 text-amber-700"
                      : "bg-zinc-100 text-zinc-500"
                  )}
                >
                  {step.order}
                </span>
                <p
                  className={cn(
                    "text-sm leading-relaxed",
                    step.is_critical
                      ? "text-zinc-900 font-medium"
                      : "text-zinc-600"
                  )}
                >
                  {step.instruction}
                  {step.is_critical && (
                    <Badge
                      variant="secondary"
                      className="ml-2 text-[9px] bg-amber-100 text-amber-700 align-middle"
                    >
                      Key Step
                    </Badge>
                  )}
                </p>
              </li>
            ))}
          </ol>
        </div>

        {/* Pairings */}
        {recipe.preferred_side_pairings.length > 0 && (
          <>
            <Separator className="mb-5" />
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-zinc-900 mb-2">
                Pairs Well With
              </h2>
              <div className="flex flex-wrap gap-2">
                {recipe.preferred_side_pairings.map((id) => (
                  <Badge key={id} variant="outline" className="text-xs">
                    {id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Links */}
        {recipe.links.length > 0 && (
          <>
            <Separator className="mb-5" />
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-zinc-900 mb-2">Links</h2>
              <ul className="space-y-2">
                {recipe.links.map((link, i) => (
                  <li key={i}>
                    <a
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </div>

      <NavBar />
    </div>
  );
}
