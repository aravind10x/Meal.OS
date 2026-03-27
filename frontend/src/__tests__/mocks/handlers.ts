/**
 * MSW (Mock Service Worker) request handlers for API mocking in tests.
 *
 * These intercept fetch calls to the backend API and return predictable test data.
 * Shapes match the ACTUAL backend API responses.
 */
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

export const MOCK_RECIPES = [
  {
    id: "sambar",
    name: "Sambar",
    cuisine_tags: ["south_indian"],
    meal_template: "south_indian",
    is_side_dish: false,
    protein_tier: "medium",
    cook_familiarity: "known",
    serves: "3-4",
    prep_time_minutes: 15,
    cook_time_minutes: 45,
  },
  {
    id: "palak_paneer",
    name: "Palak Paneer",
    cuisine_tags: ["north_indian"],
    meal_template: "north_indian",
    is_side_dish: false,
    protein_tier: "high",
    cook_familiarity: "needs_instructions",
    serves: "3-4",
    prep_time_minutes: 20,
    cook_time_minutes: 30,
  },
  {
    id: "beans_poriyal",
    name: "Beans Poriyal",
    cuisine_tags: ["south_indian"],
    meal_template: "south_indian",
    is_side_dish: true,
    protein_tier: "low",
    cook_familiarity: "known",
    serves: "3-4",
    prep_time_minutes: 10,
    cook_time_minutes: 15,
  },
];

export const MOCK_RECIPE_DETAIL = {
  id: "sambar",
  name: "Sambar",
  description: "Palakkad-style sambar with freshly ground masala",
  cuisine_tags: ["south_indian"],
  meal_template: "south_indian",
  is_side_dish: false,
  ingredients: [
    { name: "Toor Dal", quantity: "1 cup", category: "pantry", note: "" },
    { name: "Drumstick", quantity: "2 sticks", category: "vegetable", note: "cut into 3-inch pieces" },
  ],
  steps: [
    { order: 1, instruction: "Pressure cook toor dal until soft", is_critical: false },
    { order: 2, instruction: "Roast coriander seeds, chana dal, red chilies, and coconut — grind smooth", is_critical: true },
  ],
  critical_notes: "The key to this sambar is the freshly ground masala.",
  kid_adaptation: "Set aside 1-2 ladles of cooked dal before mixing with sambar for the kid.",
  preferred_side_pairings: ["beans_poriyal", "thayir_pachadi"],
  protein_tier: "medium",
  cook_familiarity: "known",
  links: [],
  recipe_audio_url: null,
  serves: "3-4",
  prep_time_minutes: 15,
  cook_time_minutes: 45,
  created_at: "2026-02-13T00:00:00Z",
  updated_at: "2026-02-13T00:00:00Z",
};

export const MOCK_TEMPLATES = [
  {
    id: "south_indian",
    name: "South Indian",
    description: "Traditional South Indian thali",
    required_components: [{ role: "main_curry", description: "Sambar/Rasam/Kootu" }],
    optional_components: [{ role: "side", description: "Poriyal or Pachadi" }],
    carb_rules: { default: "rice" },
    roti_rules: { shweta: "always" },
  },
];

// ---------------------------------------------------------------------------
// Check-in mock data (matches backend schemas/checkin.py)
// ---------------------------------------------------------------------------

export const MOCK_VEGETABLES = {
  vegetables: [
    {
      category: "Poriyal / Stir-fry",
      items: [
        { name: "French Beans", aliases: ["beans"], seasonal: false },
        { name: "Cabbage", aliases: [], seasonal: false },
        { name: "Carrot", aliases: [], seasonal: false },
      ],
    },
    {
      category: "Curry / Gravy",
      items: [
        { name: "Drumstick", aliases: ["moringa"], seasonal: true },
        { name: "Spinach", aliases: ["palak"], seasonal: false },
        { name: "Paneer", aliases: ["cottage cheese"], seasonal: false },
      ],
    },
  ],
};

export const MOCK_CHECKIN_RESPONSE = {
  plan_date: "2026-02-16",
  leftovers_logged: 1,
  veg_availability: {
    id: 1,
    snapshot_date: "2026-02-16",
    vegetables: ["French Beans", "Spinach", "Drumstick"],
    use_soon: ["Spinach"],
    created_at: "2026-02-15T22:00:00Z",
  },
  active_leftovers: [
    {
      id: 1,
      dish_name: "Yesterday's Dal",
      recipe_id: null,
      servings_estimate: "small",
      date_logged: "2026-02-16",
      status: "active",
      notes: "",
      created_at: "2026-02-15T22:00:00Z",
    },
  ],
};

export const MOCK_LATEST_CHECKIN = {
  plan_date: "2026-02-16",
  vegetables: ["French Beans", "Spinach", "Drumstick"],
  use_soon: ["Spinach"],
  active_leftovers: [
    {
      id: 1,
      dish_name: "Yesterday's Dal",
      recipe_id: null,
      servings_estimate: "small",
      date_logged: "2026-02-16",
      status: "active",
      notes: "",
      created_at: "2026-02-15T22:00:00Z",
    },
  ],
};

export const MOCK_ACTIVE_LEFTOVERS = [
  {
    id: 1,
    dish_name: "Yesterday's Dal",
    recipe_id: null,
    servings_estimate: "small",
    date_logged: "2026-02-16",
    status: "active",
    notes: "",
    created_at: "2026-02-15T22:00:00Z",
  },
];

// ---------------------------------------------------------------------------
// Planner mock data (matches backend schemas/meal_plan.py)
// ---------------------------------------------------------------------------

export const MOCK_PLAN_CANDIDATE = {
  id: 1,
  plan_date: "2026-02-16",
  status: "draft" as const,
  template_id: "south_indian",
  cuisine: "South Indian",
  dishes: [
    { recipe_id: "sambar", role: "main_curry", name: "Sambar" },
    { recipe_id: "beans_poriyal", role: "side_dish", name: "Beans Poriyal" },
    { recipe_id: "salad", role: "salad", name: "Carrot & Cucumber Salad" },
  ],
  egg_style: "omelette",
  include_curd_rice_side: false,
  roti_count: "standard batch",
  kid_notes: "Set aside dal before adding sambar masala.",
  rationale: "Classic South Indian meal, uses available beans and drumstick.",
  cook_brief_text: "",
  voice_script_text: "",
  voice_audio_url: null,
  shopping_list: [{ name: "Drumstick", category: "needed" }],
  validation: { is_valid: true, violations: [] },
  created_at: "2026-02-15T22:00:00Z",
  approved_at: null,
};

const MOCK_PLAN_CANDIDATE_2 = {
  ...MOCK_PLAN_CANDIDATE,
  id: 2,
  template_id: "north_indian",
  cuisine: "North Indian",
  dishes: [
    { recipe_id: "palak_paneer", role: "main_curry", name: "Palak Paneer" },
    { recipe_id: "salad", role: "salad", name: "Carrot & Cucumber Salad" },
  ],
  egg_style: "boiled",
  rationale: "High protein option with paneer and spinach.",
  shopping_list: [{ name: "Paneer", category: "needed" }],
};

const MOCK_PLAN_CANDIDATE_3 = {
  ...MOCK_PLAN_CANDIDATE,
  id: 3,
  template_id: "bengali",
  cuisine: "Bengali",
  dishes: [
    { recipe_id: "aloo_posto", role: "main_curry", name: "Aloo Posto" },
    { recipe_id: "salad", role: "salad", name: "Carrot & Cucumber Salad" },
  ],
  egg_style: "scrambled",
  rationale: "Comfort Bengali meal.",
  shopping_list: [],
};

export const MOCK_APPROVED_PLAN = {
  ...MOCK_PLAN_CANDIDATE,
  status: "approved" as const,
  validation: null,
  approved_at: "2026-02-15T22:30:00Z",
};

export const MOCK_APPROVE_RESPONSE = {
  plan: MOCK_APPROVED_PLAN,
  history_recorded: true,
};

export const MOCK_COOK_BRIEF = {
  plan_id: 1,
  brief_text: `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COOK BRIEF — Monday, Feb 16
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 TODAY'S MENU
• Main: Sambar
• Side: Beans Poriyal
• Roti: standard batch
• Rice: No
• Eggs: Omelette (5 eggs total)
• Salad: Carrots + Cucumber

👶 KID NOTE
• Set aside dal before adding sambar masala.`,
  voice_audio_url: null,
  voice_script_text: null,
};

export const MOCK_SHOPPING_LIST = {
  plan_id: 1,
  items: [
    { name: "Drumstick", quantity: "200g", category: "needed", for_dish: "Sambar" },
    { name: "French Beans", quantity: "250g", category: "likely_available", for_dish: "Beans Poriyal" },
    { name: "Toor Dal", quantity: "1 cup", category: "pantry_staple", for_dish: "Sambar" },
  ],
};

export const MOCK_MEAL_HISTORY = [
  {
    id: 1,
    history_date: "2026-02-15",
    meal_plan_id: null,
    dishes_cooked: ["dal_tadka", "aloo_gobi"],
    egg_style: "boiled",
    cuisine: "North Indian",
    notes: "",
    created_at: "2026-02-15T10:00:00Z",
  },
];

// ---------------------------------------------------------------------------
// Voice Script & Audio mock data (Phase 2)
// ---------------------------------------------------------------------------

export const MOCK_VOICE_SCRIPT = {
  plan_id: 1,
  script_text:
    "नमस्ते! कल ke liye: सांभर बनानी है ड्रमस्टिक और टमाटर के साथ। साथ में बीन्स पोरियल। रोटी रेगुलर बैच। अंडे — ऑमलेट बनाना है, पांच अंडे। एक छोटा हिस्सा बच्चे के लिए कम मसाले का रखना।",
};

export const MOCK_VOICE_AUDIO = {
  plan_id: 1,
  audio_url: "/api/audio/brief_1.mp3",
  script_text: MOCK_VOICE_SCRIPT.script_text,
};

// ---------------------------------------------------------------------------
// Request handlers
// ---------------------------------------------------------------------------

const API_BASE = "http://localhost:8000";

const handlers = [
  // List recipes
  http.get(`${API_BASE}/api/recipes`, ({ request }) => {
    const url = new URL(request.url);
    const cuisine = url.searchParams.get("cuisine");
    let recipes = [...MOCK_RECIPES];
    if (cuisine) {
      recipes = recipes.filter((r) => r.cuisine_tags.includes(cuisine));
    }
    return HttpResponse.json(recipes);
  }),

  // Get recipe detail
  http.get(`${API_BASE}/api/recipes/:id`, ({ params }) => {
    const { id } = params;
    if (id === "sambar") {
      return HttpResponse.json(MOCK_RECIPE_DETAIL);
    }
    return HttpResponse.json({ detail: `Recipe '${id}' not found` }, { status: 404 });
  }),

  // Create recipe
  http.post(`${API_BASE}/api/recipes`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      { ...body, created_at: "2026-02-13T00:00:00Z", updated_at: "2026-02-13T00:00:00Z" },
      { status: 201 }
    );
  }),

  // Update recipe
  http.put(`${API_BASE}/api/recipes/:id`, async ({ params, request }) => {
    const body = await request.json();
    return HttpResponse.json({ ...MOCK_RECIPE_DETAIL, ...(body as object) });
  }),

  // Delete recipe
  http.delete(`${API_BASE}/api/recipes/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // List templates
  http.get(`${API_BASE}/api/templates`, () => {
    return HttpResponse.json(MOCK_TEMPLATES);
  }),

  // Health check
  http.get(`${API_BASE}/api/health`, () => {
    return HttpResponse.json({ status: "healthy", app: "Meal.OS", version: "0.1.0" });
  }),

  // --- Vegetables reference ---
  http.get(`${API_BASE}/api/vegetables`, () => {
    return HttpResponse.json(MOCK_VEGETABLES);
  }),

  // --- Check-in (matches backend routers/checkin.py) ---
  http.post(`${API_BASE}/api/checkin`, () => {
    return HttpResponse.json(MOCK_CHECKIN_RESPONSE);
  }),

  http.get(`${API_BASE}/api/checkin/latest`, () => {
    return HttpResponse.json(MOCK_LATEST_CHECKIN);
  }),

  // Active leftovers lives under /api prefix (not /api/checkin/)
  http.get(`${API_BASE}/api/leftovers/active`, () => {
    return HttpResponse.json(MOCK_ACTIVE_LEFTOVERS);
  }),

  // --- Planner (matches backend routers/planner.py) ---
  // Generate returns list[MealPlanResponse]
  http.post(`${API_BASE}/api/planner/generate`, () => {
    return HttpResponse.json(
      [MOCK_PLAN_CANDIDATE, MOCK_PLAN_CANDIDATE_2, MOCK_PLAN_CANDIDATE_3],
    );
  }),

  http.get(`${API_BASE}/api/planner/candidates`, () => {
    return HttpResponse.json([MOCK_PLAN_CANDIDATE, MOCK_PLAN_CANDIDATE_2, MOCK_PLAN_CANDIDATE_3]);
  }),

  // Approved plan — returns the approved plan or null
  http.get(`${API_BASE}/api/planner/approved`, () => {
    return HttpResponse.json(null);
  }),

  // Approve returns MealPlanApproveResponse { plan, history_recorded }
  http.post(`${API_BASE}/api/planner/approve/:planId`, () => {
    return HttpResponse.json(MOCK_APPROVE_RESPONSE);
  }),

  http.post(`${API_BASE}/api/planner/swap`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({
      ...MOCK_PLAN_CANDIDATE,
      dishes: MOCK_PLAN_CANDIDATE.dishes.map((d) =>
        d.recipe_id === body.old_recipe_id
          ? { recipe_id: body.new_recipe_id, name: body.new_recipe_name, role: body.new_role }
          : d
      ),
    });
  }),

  // Swap options — returns alternative recipes for a dish role
  http.get(`${API_BASE}/api/planner/:planId/swap-options`, ({ request }) => {
    const url = new URL(request.url);
    const recipeId = url.searchParams.get("recipe_id");
    // Return alternatives based on the recipe being swapped
    const isSide = recipeId === "beans_poriyal";
    const alternatives = isSide
      ? [
          { id: "thayir_pachadi", name: "Thayir Pachadi", cuisine_tags: ["south_indian"], meal_template: "south_indian", is_side_dish: true, protein_tier: "low", cook_familiarity: "known" },
          { id: "carrot_kosambari", name: "Carrot Kosambari", cuisine_tags: ["south_indian"], meal_template: "south_indian", is_side_dish: true, protein_tier: "low", cook_familiarity: "known" },
        ]
      : [
          { id: "rasam", name: "Rasam", cuisine_tags: ["south_indian"], meal_template: "south_indian", is_side_dish: false, protein_tier: "medium", cook_familiarity: "known" },
          { id: "avial", name: "Avial", cuisine_tags: ["south_indian"], meal_template: "south_indian", is_side_dish: false, protein_tier: "medium", cook_familiarity: "needs_instructions" },
          { id: "palak_paneer", name: "Palak Paneer", cuisine_tags: ["north_indian"], meal_template: "north_indian", is_side_dish: false, protein_tier: "high", cook_familiarity: "needs_instructions" },
        ];
    return HttpResponse.json(alternatives);
  }),

  // Toggle curd rice
  http.patch(`${API_BASE}/api/planner/:planId/curd-rice`, async ({ request }) => {
    const body = (await request.json()) as { include: boolean };
    return HttpResponse.json({
      ...MOCK_PLAN_CANDIDATE,
      include_curd_rice_side: body.include,
    });
  }),

  // Meal history lives under /api prefix (not /api/planner/)
  http.get(`${API_BASE}/api/meal-history`, () => {
    return HttpResponse.json(MOCK_MEAL_HISTORY);
  }),

  // --- Cook Brief (returns { plan_id, brief_text }) ---
  http.get(`${API_BASE}/api/brief/:planId`, () => {
    return HttpResponse.json(MOCK_COOK_BRIEF);
  }),

  // --- Shopping ---
  http.get(`${API_BASE}/api/shopping/:planId`, () => {
    return HttpResponse.json(MOCK_SHOPPING_LIST);
  }),

  // --- Voice Script & Audio (Phase 2) ---
  http.get(`${API_BASE}/api/voice-script/:planId`, () => {
    return HttpResponse.json(MOCK_VOICE_SCRIPT);
  }),

  http.get(`${API_BASE}/api/voice-audio/:planId`, () => {
    return HttpResponse.json(MOCK_VOICE_AUDIO);
  }),

  // Serve audio file (returns binary blob)
  http.get(`${API_BASE}/api/audio/:filename`, () => {
    return new HttpResponse(new Blob(["fake audio data"], { type: "audio/mpeg" }), {
      headers: { "Content-Type": "audio/mpeg" },
    });
  }),

  // Recipe audio upload
  http.post(`${API_BASE}/api/recipes/:id/audio`, ({ params }) => {
    return HttpResponse.json({
      recipe_id: params.id,
      audio_url: `/api/audio/recipes/${params.id}.mp3`,
      filename: `${params.id}.mp3`,
    });
  }),

  // Recipe familiarity toggle
  http.patch(`${API_BASE}/api/recipes/:id/familiarity`, async ({ params, request }) => {
    const body = (await request.json()) as { cook_familiarity: string };
    return HttpResponse.json({
      id: params.id,
      name: "Test Recipe",
      cook_familiarity: body.cook_familiarity,
    });
  }),
];

export const server = setupServer(...handlers);
