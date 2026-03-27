const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  // Handle 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json();
}

// --- Recipes ---

import type {
  Recipe,
  RecipeListItem,
  RecipeCreate,
  RecipeUpdate,
  MealTemplate,
  CheckinRequest,
  CheckinResponse,
  LatestCheckinResponse,
  LeftoverResponse,
  MealPlanResponse,
  GeneratePlansRequest,
  MealPlanApproveResponse,
  SwapDishRequest,
  SwapOptionItem,
  CurdRiceToggleRequest,
  MealHistoryResponse,
  ShoppingListResponse,
  CookBriefResponse,
  VegetableCategory,
  VoiceScriptResponse,
  VoiceAudioResponse,
  RecipeAudioUploadResponse,
  FamiliarityToggleResponse,
} from "@/types";

export const api = {
  recipes: {
    list: (params?: { cuisine?: string; template?: string; side_only?: boolean }) => {
      const searchParams = new URLSearchParams();
      if (params?.cuisine) searchParams.set("cuisine", params.cuisine);
      if (params?.template) searchParams.set("template", params.template);
      if (params?.side_only !== undefined) searchParams.set("side_only", String(params.side_only));
      const query = searchParams.toString();
      return fetchAPI<RecipeListItem[]>(`/api/recipes${query ? `?${query}` : ""}`);
    },

    get: (id: string) => fetchAPI<Recipe>(`/api/recipes/${id}`),

    create: (data: RecipeCreate) =>
      fetchAPI<Recipe>("/api/recipes", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    update: (id: string, data: RecipeUpdate) =>
      fetchAPI<Recipe>(`/api/recipes/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),

    delete: (id: string) =>
      fetchAPI<void>(`/api/recipes/${id}`, { method: "DELETE" }),
  },

  templates: {
    list: () => fetchAPI<MealTemplate[]>("/api/templates"),
  },

  // --- Check-in ---
  checkin: {
    submit: (data: CheckinRequest) =>
      fetchAPI<CheckinResponse>("/api/checkin", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    latest: () => fetchAPI<LatestCheckinResponse>("/api/checkin/latest"),

    activeLeftovers: () =>
      fetchAPI<LeftoverResponse[]>("/api/leftovers/active"),
  },

  // --- Vegetables reference ---
  vegetables: {
    list: () => fetchAPI<{ vegetables: VegetableCategory[] }>("/api/vegetables"),
  },

  // --- Planner ---
  planner: {
    generate: (data: GeneratePlansRequest) =>
      fetchAPI<MealPlanResponse[]>("/api/planner/generate", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    candidates: (planDate?: string) => {
      const params = planDate ? `?plan_date=${planDate}` : "";
      return fetchAPI<MealPlanResponse[]>(`/api/planner/candidates${params}`);
    },

    approved: (planDate: string) =>
      fetchAPI<MealPlanResponse | null>(`/api/planner/approved?plan_date=${planDate}`),

    approve: (planId: number) =>
      fetchAPI<MealPlanApproveResponse>(`/api/planner/approve/${planId}`, {
        method: "POST",
      }),

    swap: (data: SwapDishRequest) =>
      fetchAPI<MealPlanResponse>("/api/planner/swap", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    swapOptions: (planId: number, recipeId: string) =>
      fetchAPI<SwapOptionItem[]>(
        `/api/planner/${planId}/swap-options?recipe_id=${recipeId}`
      ),

    toggleCurdRice: (planId: number, include: boolean) =>
      fetchAPI<MealPlanResponse>(`/api/planner/${planId}/curd-rice`, {
        method: "PATCH",
        body: JSON.stringify({ include } satisfies CurdRiceToggleRequest),
      }),

    history: (limit?: number) => {
      const params = limit ? `?limit=${limit}` : "";
      return fetchAPI<MealHistoryResponse[]>(`/api/meal-history${params}`);
    },
  },

  // --- Cook Brief ---
  brief: {
    get: (planId: number) => fetchAPI<CookBriefResponse>(`/api/brief/${planId}`),
  },

  // --- Voice Script & Audio ---
  voice: {
    getScript: (planId: number) =>
      fetchAPI<VoiceScriptResponse>(`/api/voice-script/${planId}`),

    getAudio: (planId: number) =>
      fetchAPI<VoiceAudioResponse>(`/api/voice-audio/${planId}`),

    /** Download audio file as a Blob (for share/download). */
    downloadAudio: async (audioUrl: string): Promise<Blob> => {
      const res = await fetch(`${API_BASE}${audioUrl}`);
      if (!res.ok) throw new Error("Failed to download audio");
      return res.blob();
    },
  },

  // --- Recipe Audio ---
  recipeAudio: {
    upload: async (recipeId: string, file: File): Promise<RecipeAudioUploadResponse> => {
      const formData = new FormData();
      formData.append("audio_file", file);
      const res = await fetch(`${API_BASE}/api/recipes/${recipeId}/audio`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `Upload failed: ${res.status}`);
      }
      return res.json();
    },

    getUrl: (recipeId: string) =>
      fetchAPI<{ recipe_audio_url: string | null }>(`/api/recipes/${recipeId}`).then(
        (r) => (r as unknown as Recipe).recipe_audio_url
      ),
  },

  // --- Recipe Familiarity ---
  familiarity: {
    toggle: (recipeId: string, familiarity: "known" | "needs_instructions" | "new") =>
      fetchAPI<FamiliarityToggleResponse>(`/api/recipes/${recipeId}/familiarity`, {
        method: "PATCH",
        body: JSON.stringify({ cook_familiarity: familiarity }),
      }),
  },

  // --- Shopping ---
  shopping: {
    get: (planId: number) =>
      fetchAPI<ShoppingListResponse>(`/api/shopping/${planId}`),
  },

  health: () => fetchAPI<{ status: string; app: string; version: string }>("/api/health"),
};
