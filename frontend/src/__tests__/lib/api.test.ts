/**
 * Tests for the API client module.
 *
 * Uses MSW to intercept network requests and return mock data.
 * Verifies: correct URL construction, query params, error handling.
 */
import { describe, it, expect } from "vitest";
import { api } from "@/lib/api";
import { server } from "../mocks/handlers";
import { http, HttpResponse } from "msw";

describe("api.recipes", () => {
  describe("list", () => {
    it("should fetch all recipes", async () => {
      const recipes = await api.recipes.list();
      expect(recipes).toBeInstanceOf(Array);
      expect(recipes.length).toBe(3);
      expect(recipes[0].id).toBe("sambar");
    });

    it("should filter by cuisine", async () => {
      const recipes = await api.recipes.list({ cuisine: "south_indian" });
      expect(recipes.length).toBe(2); // sambar + beans_poriyal
      recipes.forEach((r) => {
        expect(r.cuisine_tags).toContain("south_indian");
      });
    });
  });

  describe("get", () => {
    it("should fetch recipe detail by id", async () => {
      const recipe = await api.recipes.get("sambar");
      expect(recipe.id).toBe("sambar");
      expect(recipe.name).toBe("Sambar");
      expect(recipe.ingredients).toBeDefined();
      expect(recipe.steps).toBeDefined();
    });

    it("should throw on 404", async () => {
      await expect(api.recipes.get("nonexistent")).rejects.toThrow();
    });
  });

  describe("create", () => {
    it("should create a recipe", async () => {
      const recipe = await api.recipes.create({
        id: "test_new",
        name: "Test New Recipe",
      });
      expect(recipe.id).toBe("test_new");
      expect(recipe.name).toBe("Test New Recipe");
    });
  });

  describe("update", () => {
    it("should update a recipe", async () => {
      const recipe = await api.recipes.update("sambar", { name: "Updated Sambar" });
      expect(recipe.name).toBe("Updated Sambar");
    });
  });

  describe("delete", () => {
    it("should delete a recipe without error", async () => {
      await expect(api.recipes.delete("sambar")).resolves.not.toThrow();
    });
  });
});

describe("api.templates", () => {
  it("should fetch all templates", async () => {
    const templates = await api.templates.list();
    expect(templates).toBeInstanceOf(Array);
    expect(templates.length).toBeGreaterThan(0);
    expect(templates[0].id).toBe("south_indian");
  });
});

describe("api.health", () => {
  it("should return health status", async () => {
    const health = await api.health();
    expect(health.status).toBe("healthy");
    expect(health.app).toBe("Meal.OS");
  });
});

describe("api error handling", () => {
  it("should throw on server error", async () => {
    server.use(
      http.get("http://localhost:8000/api/recipes", () => {
        return HttpResponse.json({ detail: "Internal server error" }, { status: 500 });
      })
    );

    await expect(api.recipes.list()).rejects.toThrow("Internal server error");
  });
});
