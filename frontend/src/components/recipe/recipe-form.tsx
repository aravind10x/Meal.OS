"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Trash2 } from "lucide-react";
import {
  type RecipeCreate,
  type IngredientItem,
  type StepItem,
  CUISINE_LABELS,
} from "@/types";
import { cn } from "@/lib/utils";

// --- Types ---

type CuisineTag = keyof typeof CUISINE_LABELS;

const CUISINE_OPTIONS: { value: CuisineTag; label: string }[] = [
  { value: "south_indian", label: "South Indian" },
  { value: "north_indian", label: "North Indian" },
  { value: "indo_chinese", label: "Indo-Chinese" },
  { value: "bengali", label: "Bengali" },
  { value: "comfort", label: "Comfort" },
];

const TEMPLATE_OPTIONS = [
  { value: "south_indian", label: "South Indian" },
  { value: "north_indian", label: "North Indian" },
  { value: "indo_chinese", label: "Indo-Chinese" },
  { value: "bengali", label: "Bengali" },
  { value: "comfort", label: "Comfort" },
];

const PROTEIN_OPTIONS = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

const FAMILIARITY_OPTIONS = [
  { value: "new", label: "New Recipe" },
  { value: "needs_instructions", label: "Needs Instructions" },
  { value: "known", label: "Cook Knows" },
];

// --- Props ---

interface RecipeFormProps {
  initialData?: Partial<RecipeCreate>;
  /** When true, the ID field is editable (for new recipes) */
  isNew?: boolean;
  onSubmit: (data: RecipeCreate) => Promise<void>;
  onCancel: () => void;
  submitLabel?: string;
}

// --- Helper to generate slug from name ---
function toSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s_]/g, "")
    .replace(/\s+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_|_$/g, "");
}

// --- Component ---

export function RecipeForm({
  initialData,
  isNew = true,
  onSubmit,
  onCancel,
  submitLabel = "Save Recipe",
}: RecipeFormProps) {
  // --- Form state ---
  const [id, setId] = useState(initialData?.id ?? "");
  const [name, setName] = useState(initialData?.name ?? "");
  const [description, setDescription] = useState(initialData?.description ?? "");
  const [cuisineTags, setCuisineTags] = useState<string[]>(
    initialData?.cuisine_tags ?? []
  );
  const [mealTemplate, setMealTemplate] = useState(
    initialData?.meal_template ?? ""
  );
  const [isSideDish, setIsSideDish] = useState(
    initialData?.is_side_dish ?? false
  );
  const [ingredients, setIngredients] = useState<IngredientItem[]>(
    initialData?.ingredients ?? []
  );
  const [steps, setSteps] = useState<StepItem[]>(initialData?.steps ?? []);
  const [criticalNotes, setCriticalNotes] = useState(
    initialData?.critical_notes ?? ""
  );
  const [kidAdaptation, setKidAdaptation] = useState(
    initialData?.kid_adaptation ?? ""
  );
  const [sidePairings, setSidePairings] = useState(
    (initialData?.preferred_side_pairings ?? []).join(", ")
  );
  const [proteinTier, setProteinTier] = useState(
    initialData?.protein_tier ?? "medium"
  );
  const [cookFamiliarity, setCookFamiliarity] = useState(
    initialData?.cook_familiarity ?? "needs_instructions"
  );
  const [links, setLinks] = useState((initialData?.links ?? []).join("\n"));
  const [serves, setServes] = useState(initialData?.serves ?? "3-4");
  const [prepTime, setPrepTime] = useState<string>(
    initialData?.prep_time_minutes?.toString() ?? ""
  );
  const [cookTime, setCookTime] = useState<string>(
    initialData?.cook_time_minutes?.toString() ?? ""
  );

  const [submitting, setSubmitting] = useState(false);
  const [autoSlug, setAutoSlug] = useState(isNew);

  // --- Cuisine tag toggle ---
  const toggleCuisine = (tag: string) => {
    setCuisineTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  // --- Ingredient helpers ---
  const addIngredient = () => {
    setIngredients((prev) => [
      ...prev,
      { name: "", quantity: "", category: "vegetable" as const, note: "" },
    ]);
  };

  const updateIngredient = (
    index: number,
    field: keyof IngredientItem,
    value: string | string[]
  ) => {
    setIngredients((prev) =>
      prev.map((ing, i) => (i === index ? { ...ing, [field]: value } : ing))
    );
  };

  const removeIngredient = (index: number) => {
    setIngredients((prev) => prev.filter((_, i) => i !== index));
  };

  // --- Step helpers ---
  const addStep = () => {
    setSteps((prev) => [
      ...prev,
      { order: prev.length + 1, instruction: "", is_critical: false },
    ]);
  };

  const updateStep = (
    index: number,
    field: keyof StepItem,
    value: string | number | boolean
  ) => {
    setSteps((prev) =>
      prev.map((step, i) =>
        i === index ? { ...step, [field]: value } : step
      )
    );
  };

  const removeStep = (index: number) => {
    setSteps((prev) =>
      prev
        .filter((_, i) => i !== index)
        .map((step, i) => ({ ...step, order: i + 1 }))
    );
  };

  // --- Name change auto-slug ---
  const handleNameChange = (newName: string) => {
    setName(newName);
    if (isNew && autoSlug) {
      setId(toSlug(newName));
    }
  };

  // --- Submit ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const data: RecipeCreate = {
        id: isNew ? id : initialData?.id ?? id,
        name,
        description,
        cuisine_tags: cuisineTags,
        meal_template: mealTemplate,
        is_side_dish: isSideDish,
        ingredients: ingredients.filter((i) => i.name.trim()),
        steps: steps.filter((s) => s.instruction.trim()),
        critical_notes: criticalNotes,
        kid_adaptation: kidAdaptation,
        preferred_side_pairings: sidePairings
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        protein_tier: proteinTier,
        cook_familiarity: cookFamiliarity,
        links: links
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean),
        serves,
        prep_time_minutes: prepTime ? parseInt(prepTime, 10) : null,
        cook_time_minutes: cookTime ? parseInt(cookTime, 10) : null,
      };

      await onSubmit(data);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic info */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-zinc-900">Basic Info</h2>

        <div className="space-y-2">
          <Label htmlFor="recipe-name">Recipe Name *</Label>
          <Input
            id="recipe-name"
            placeholder="e.g., Sambar"
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            required
          />
        </div>

        {isNew && (
          <div className="space-y-2">
            <Label htmlFor="recipe-id">Recipe ID (slug) *</Label>
            <div className="flex gap-2 items-center">
              <Input
                id="recipe-id"
                placeholder="e.g., sambar"
                value={id}
                onChange={(e) => {
                  setAutoSlug(false);
                  setId(e.target.value);
                }}
                required
                pattern="^[a-z][a-z0-9_]*$"
                title="Lowercase letters, numbers, and underscores only"
                className="font-mono text-sm"
              />
            </div>
            <p className="text-xs text-zinc-400">
              Auto-generated from name. Lowercase letters, numbers, underscores only.
            </p>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="recipe-desc">Description</Label>
          <Textarea
            id="recipe-desc"
            placeholder="Brief description of this dish..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
          />
        </div>
      </section>

      <Separator />

      {/* Classification */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-zinc-900">Classification</h2>

        <div className="space-y-2">
          <Label>Cuisine Tags</Label>
          <div className="flex flex-wrap gap-2">
            {CUISINE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => toggleCuisine(opt.value)}
                className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-medium border transition-colors",
                  cuisineTags.includes(opt.value)
                    ? "bg-zinc-900 text-white border-zinc-900"
                    : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-300"
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Meal Template</Label>
            <Select value={mealTemplate} onValueChange={setMealTemplate}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select template" />
              </SelectTrigger>
              <SelectContent>
                {TEMPLATE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Protein Tier</Label>
            <Select value={proteinTier} onValueChange={setProteinTier}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PROTEIN_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Cook Familiarity</Label>
            <Select value={cookFamiliarity} onValueChange={setCookFamiliarity}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FAMILIARITY_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-end pb-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isSideDish}
                onChange={(e) => setIsSideDish(e.target.checked)}
                className="rounded border-zinc-300"
              />
              <span className="text-sm text-zinc-700">Side dish</span>
            </label>
          </div>
        </div>
      </section>

      <Separator />

      {/* Ingredients */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900">Ingredients</h2>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addIngredient}
            className="rounded-full"
          >
            <Plus className="h-3.5 w-3.5 mr-1" />
            Add
          </Button>
        </div>

        {ingredients.length === 0 && (
          <p className="text-sm text-zinc-400 text-center py-4">
            No ingredients yet. Click Add to start.
          </p>
        )}

        <div className="space-y-3">
          {ingredients.map((ing, i) => (
            <div
              key={i}
              className="bg-zinc-50 rounded-lg p-3 space-y-2 border border-zinc-100"
            >
              <div className="flex items-start gap-2">
                <div className="flex-1 grid grid-cols-2 gap-2">
                  <Input
                    placeholder="Ingredient name *"
                    value={ing.name}
                    onChange={(e) => updateIngredient(i, "name", e.target.value)}
                    className="text-sm"
                  />
                  <Input
                    placeholder="Quantity"
                    value={ing.quantity}
                    onChange={(e) =>
                      updateIngredient(i, "quantity", e.target.value)
                    }
                    className="text-sm"
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeIngredient(i)}
                  className="text-zinc-400 hover:text-red-500 mt-0.5"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
              <div className="flex gap-2 items-center">
                <Select
                  value={ing.category}
                  onValueChange={(v) => updateIngredient(i, "category", v)}
                >
                  <SelectTrigger className="w-32 h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="vegetable">Vegetable</SelectItem>
                    <SelectItem value="pantry">Pantry</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Note (optional)"
                  value={ing.note ?? ""}
                  onChange={(e) => updateIngredient(i, "note", e.target.value)}
                  className="text-xs h-8 flex-1"
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <Separator />

      {/* Steps */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900">Steps</h2>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addStep}
            className="rounded-full"
          >
            <Plus className="h-3.5 w-3.5 mr-1" />
            Add Step
          </Button>
        </div>

        {steps.length === 0 && (
          <p className="text-sm text-zinc-400 text-center py-4">
            No steps yet. Click Add Step to start.
          </p>
        )}

        <div className="space-y-3">
          {steps.map((step, i) => (
            <div
              key={i}
              className="flex gap-2 items-start"
            >
              <span className="w-6 h-6 rounded-full bg-zinc-100 text-zinc-500 text-xs font-bold flex items-center justify-center mt-2 flex-shrink-0">
                {step.order}
              </span>
              <div className="flex-1 space-y-1">
                <Textarea
                  placeholder={`Step ${step.order} instruction...`}
                  value={step.instruction}
                  onChange={(e) =>
                    updateStep(i, "instruction", e.target.value)
                  }
                  rows={2}
                  className="text-sm"
                />
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={step.is_critical}
                    onChange={(e) =>
                      updateStep(i, "is_critical", e.target.checked)
                    }
                    className="rounded border-zinc-300"
                  />
                  <span className="text-xs text-zinc-500">Key step</span>
                </label>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeStep(i)}
                className="text-zinc-400 hover:text-red-500 mt-2"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))}
        </div>
      </section>

      <Separator />

      {/* Notes */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-zinc-900">Notes & Extras</h2>

        <div className="space-y-2">
          <Label htmlFor="critical-notes">Critical Notes</Label>
          <Textarea
            id="critical-notes"
            placeholder="House-style taste constraints, special techniques..."
            value={criticalNotes}
            onChange={(e) => setCriticalNotes(e.target.value)}
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="kid-adaptation">Kid Adaptation</Label>
          <Textarea
            id="kid-adaptation"
            placeholder="e.g., Set aside dal before adding masala paste..."
            value={kidAdaptation}
            onChange={(e) => setKidAdaptation(e.target.value)}
            rows={2}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="side-pairings">Side Pairings</Label>
          <Input
            id="side-pairings"
            placeholder="beans_poriyal, cabbage_poriyal (comma-separated slugs)"
            value={sidePairings}
            onChange={(e) => setSidePairings(e.target.value)}
            className="font-mono text-sm"
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-2">
            <Label htmlFor="serves">Serves</Label>
            <Input
              id="serves"
              placeholder="3-4"
              value={serves}
              onChange={(e) => setServes(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="prep-time">Prep (min)</Label>
            <Input
              id="prep-time"
              type="number"
              min={0}
              placeholder="10"
              value={prepTime}
              onChange={(e) => setPrepTime(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="cook-time">Cook (min)</Label>
            <Input
              id="cook-time"
              type="number"
              min={0}
              placeholder="30"
              value={cookTime}
              onChange={(e) => setCookTime(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="links">Links</Label>
          <Textarea
            id="links"
            placeholder="YouTube links, one per line..."
            value={links}
            onChange={(e) => setLinks(e.target.value)}
            rows={2}
          />
        </div>
      </section>

      <Separator />

      {/* Actions */}
      <div className="flex gap-3 pb-4">
        <Button
          type="submit"
          disabled={submitting || !name.trim() || (isNew && !id.trim())}
          className="flex-1"
        >
          {submitting ? "Saving..." : submitLabel}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
