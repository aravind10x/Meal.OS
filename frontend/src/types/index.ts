// --- Recipe types ---

export interface IngredientItem {
  name: string;
  quantity: string;
  category: "pantry" | "vegetable";
  note?: string;
  flexible_with?: string[];
}

export interface StepItem {
  order: number;
  instruction: string;
  is_critical: boolean;
}

export interface RecipeListItem {
  id: string;
  name: string;
  cuisine_tags: string[];
  meal_template: string;
  is_side_dish: boolean;
  protein_tier: "low" | "medium" | "high";
  cook_familiarity: "known" | "needs_instructions" | "new";
  serves: string;
  prep_time_minutes: number | null;
  cook_time_minutes: number | null;
}

export interface Recipe extends RecipeListItem {
  description: string;
  ingredients: IngredientItem[];
  steps: StepItem[];
  critical_notes: string;
  kid_adaptation: string;
  preferred_side_pairings: string[];
  links: string[];
  recipe_audio_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecipeCreate {
  id: string;
  name: string;
  description?: string;
  cuisine_tags?: string[];
  meal_template?: string;
  is_side_dish?: boolean;
  ingredients?: IngredientItem[];
  steps?: StepItem[];
  critical_notes?: string;
  kid_adaptation?: string;
  preferred_side_pairings?: string[];
  protein_tier?: string;
  cook_familiarity?: string;
  links?: string[];
  serves?: string;
  prep_time_minutes?: number | null;
  cook_time_minutes?: number | null;
}

export type RecipeUpdate = Partial<Omit<Recipe, "id" | "created_at" | "updated_at">>;

// --- Meal Template types ---

export interface MealTemplateComponent {
  role: string;
  description: string;
}

export interface MealTemplate {
  id: string;
  name: string;
  description: string;
  required_components: MealTemplateComponent[];
  optional_components: MealTemplateComponent[];
  carb_rules: Record<string, string>;
  roti_rules: Record<string, unknown>;
}

// --- UI helper types ---

export type CuisineTag = "south_indian" | "north_indian" | "indo_chinese" | "bengali" | "comfort" | "international";

export const CUISINE_LABELS: Record<string, string> = {
  south_indian: "South Indian",
  north_indian: "North Indian",
  indo_chinese: "Indo-Chinese",
  bengali: "Bengali",
  comfort: "Comfort",
  international: "International",
};

export const CUISINE_COLORS: Record<string, string> = {
  south_indian: "bg-amber-100 text-amber-800",
  north_indian: "bg-red-100 text-red-800",
  indo_chinese: "bg-orange-100 text-orange-800",
  bengali: "bg-green-100 text-green-800",
  comfort: "bg-blue-100 text-blue-800",
  international: "bg-purple-100 text-purple-800",
};

export const PROTEIN_LABELS: Record<string, string> = {
  low: "Low Protein",
  medium: "Med Protein",
  high: "High Protein",
};

export const PROTEIN_COLORS: Record<string, string> = {
  low: "bg-slate-100 text-slate-600",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-emerald-100 text-emerald-700",
};

export const FAMILIARITY_LABELS: Record<string, string> = {
  known: "Cook Knows",
  needs_instructions: "Needs Instructions",
  new: "New Recipe",
};

// --- Check-in types (matches backend schemas/checkin.py) ---

export type ServingsEstimate = "small" | "1_serving" | "2_plus_servings";

export interface LeftoverItem {
  dish_name: string;
  recipe_id?: string | null;
  servings_estimate: ServingsEstimate;
  notes: string;
}

export interface CheckinRequest {
  plan_date: string; // YYYY-MM-DD
  leftovers: LeftoverItem[];
  vegetables: string[];
  use_soon: string[];
}

export interface LeftoverResponse {
  id: number;
  dish_name: string;
  recipe_id: string | null;
  servings_estimate: string;
  date_logged: string;
  status: string;
  notes: string;
  created_at: string;
}

export interface VegAvailabilityResponse {
  id: number;
  snapshot_date: string;
  vegetables: string[];
  use_soon: string[];
  created_at: string;
}

export interface CheckinResponse {
  plan_date: string;
  leftovers_logged: number;
  veg_availability: VegAvailabilityResponse;
  active_leftovers: LeftoverResponse[];
}

export interface LatestCheckinResponse {
  plan_date: string;
  vegetables: string[];
  use_soon: string[];
  active_leftovers: LeftoverResponse[];
}

// --- Meal Plan types (matches backend schemas/meal_plan.py) ---

export interface DishEntry {
  recipe_id: string;
  role: string;
  name: string;
}

export interface ValidationInfo {
  is_valid: boolean;
  violations: string[];
}

export interface MealPlanResponse {
  id: number;
  plan_date: string;
  status: string;
  template_id: string;
  cuisine: string;
  dishes: DishEntry[];
  egg_style: string;
  include_curd_rice_side: boolean;
  roti_count: string;
  kid_notes: string;
  rationale: string;
  cook_brief_text: string;
  voice_script_text: string;
  voice_audio_url: string | null;
  shopping_list: Record<string, unknown>[];
  validation: ValidationInfo | null;
  created_at: string;
  approved_at: string | null;
}

export interface GeneratePlansRequest {
  plan_date: string; // YYYY-MM-DD
  vegetables?: string[];
  use_soon?: string[];
  leftovers?: Record<string, unknown>[];
}

export interface MealPlanApproveResponse {
  plan: MealPlanResponse;
  history_recorded: boolean;
}

export interface SwapDishRequest {
  plan_id: number;
  old_recipe_id: string;
  new_recipe_id: string;
  new_recipe_name: string;
  new_role: string;
}

export interface SwapOptionItem {
  id: string;
  name: string;
  cuisine_tags: string[];
  meal_template: string;
  is_side_dish: boolean;
  protein_tier: string;
  cook_familiarity: string;
}

export interface CurdRiceToggleRequest {
  include: boolean;
}

export interface MealHistoryResponse {
  id: number;
  history_date: string;
  meal_plan_id: number | null;
  dishes_cooked: string[];
  egg_style: string;
  cuisine: string;
  notes: string;
  created_at: string;
}

// --- Shopping List types (matches backend routers/shopping.py) ---

export interface ShoppingItem {
  name: string;
  quantity: string;
  category: "needed" | "likely_available" | "pantry_staple";
  for_dish: string;
}

export interface ShoppingListResponse {
  plan_id: number;
  items: ShoppingItem[];
}

// --- Cook Brief types (matches backend routers/cook_brief.py) ---

export interface CookBriefResponse {
  plan_id: number;
  brief_text: string;
  voice_audio_url: string | null;
  voice_script_text: string | null;
}

// --- Voice Script types (matches backend routers/voice.py) ---

export interface VoiceScriptResponse {
  plan_id: number;
  script_text: string;
}

export interface VoiceAudioResponse {
  plan_id: number;
  audio_url: string | null;
  script_text: string;
  tts_error?: string;
}

// --- Recipe Audio types ---

export interface RecipeAudioUploadResponse {
  recipe_id: string;
  audio_url: string;
  filename: string;
}

// --- Familiarity Toggle types ---

export interface FamiliarityToggleResponse {
  id: string;
  name: string;
  cook_familiarity: "known" | "needs_instructions" | "new";
}

// --- Vegetable reference types ---

export interface VegetableItem {
  name: string;
  aliases: string[];
  seasonal: boolean;
}

export interface VegetableCategory {
  category: string;
  items: VegetableItem[];
}
