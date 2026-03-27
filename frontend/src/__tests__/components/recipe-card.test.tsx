/**
 * Tests for RecipeCard component.
 *
 * Verifies: recipe name display, cuisine tags, protein tier badge,
 * time display, side dish badge, and link target.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { RecipeCard } from "@/components/recipe/recipe-card";
import type { RecipeListItem } from "@/types";

// Mock Next.js Link to render a plain <a> tag
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

const baseRecipe: RecipeListItem = {
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
};

describe("RecipeCard", () => {
  it("should display the recipe name", () => {
    render(<RecipeCard recipe={baseRecipe} />);
    expect(screen.getByText("Sambar")).toBeInTheDocument();
  });

  it("should display cuisine tag labels", () => {
    render(<RecipeCard recipe={baseRecipe} />);
    expect(screen.getByText("South Indian")).toBeInTheDocument();
  });

  it("should display protein tier badge", () => {
    render(<RecipeCard recipe={baseRecipe} />);
    expect(screen.getByText("Med Protein")).toBeInTheDocument();
  });

  it("should show total cook time", () => {
    render(<RecipeCard recipe={baseRecipe} />);
    expect(screen.getByText("60m")).toBeInTheDocument();
  });

  it("should not show time when both times are null", () => {
    const recipe = { ...baseRecipe, prep_time_minutes: null, cook_time_minutes: null };
    render(<RecipeCard recipe={recipe} />);
    expect(screen.queryByText("0m")).not.toBeInTheDocument();
  });

  it("should show 'Side Dish' badge for side dishes", () => {
    const sideRecipe = { ...baseRecipe, is_side_dish: true };
    render(<RecipeCard recipe={sideRecipe} />);
    expect(screen.getByText("Side Dish")).toBeInTheDocument();
  });

  it("should not show 'Side Dish' badge for main dishes", () => {
    render(<RecipeCard recipe={baseRecipe} />);
    expect(screen.queryByText("Side Dish")).not.toBeInTheDocument();
  });

  it("should link to the recipe detail page", () => {
    render(<RecipeCard recipe={baseRecipe} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/recipes/sambar");
  });

  it("should display multiple cuisine tags", () => {
    const multiTagRecipe = { ...baseRecipe, cuisine_tags: ["south_indian", "comfort"] };
    render(<RecipeCard recipe={multiTagRecipe} />);
    expect(screen.getByText("South Indian")).toBeInTheDocument();
    expect(screen.getByText("Comfort")).toBeInTheDocument();
  });

  it("should display high protein badge correctly", () => {
    const highProtein = { ...baseRecipe, protein_tier: "high" as const };
    render(<RecipeCard recipe={highProtein} />);
    expect(screen.getByText("High Protein")).toBeInTheDocument();
  });
});
