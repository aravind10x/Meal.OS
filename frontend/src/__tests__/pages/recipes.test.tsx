/**
 * Tests for the Recipes list page.
 *
 * Verifies: data loading, recipe display, cuisine filtering, type toggle,
 * loading skeleton, empty state, add recipe button.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RecipesPage from "@/app/recipes/page";
import { MOCK_RECIPES } from "../mocks/handlers";

// Mock Next.js dependencies
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/recipes",
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({}),
}));

describe("RecipesPage", () => {
  it("should show loading skeletons initially", () => {
    render(<RecipesPage />);
    // Skeleton elements are animated pulse divs
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("should display recipe cards after loading", async () => {
    render(<RecipesPage />);
    await waitFor(() => {
      expect(screen.getByText("Sambar")).toBeInTheDocument();
    });
    expect(screen.getByText("Palak Paneer")).toBeInTheDocument();
    expect(screen.getByText("Beans Poriyal")).toBeInTheDocument();
  });

  it("should show the correct recipe count", async () => {
    render(<RecipesPage />);
    await waitFor(() => {
      expect(
        screen.getByText(`${MOCK_RECIPES.length} house-style recipes`)
      ).toBeInTheDocument();
    });
  });

  it("should have an Add button that links to /recipes/new", async () => {
    render(<RecipesPage />);
    await waitFor(() => {
      expect(screen.getByText("Sambar")).toBeInTheDocument();
    });
    const addLink = screen.getByRole("link", { name: /add/i });
    expect(addLink).toHaveAttribute("href", "/recipes/new");
  });

  it("should show cuisine filter buttons", async () => {
    render(<RecipesPage />);
    await waitFor(() => {
      expect(screen.getByText("Sambar")).toBeInTheDocument();
    });
    // Cuisine names appear both in filter buttons and in recipe card badges.
    // Just verify they appear at least once (filter button + maybe badges).
    const allButtons = screen.getAllByText("All");
    expect(allButtons.length).toBeGreaterThanOrEqual(2); // cuisine filter + type toggle
    expect(screen.getAllByText("South Indian").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("North Indian").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Indo-Chinese")).toBeInTheDocument();
    expect(screen.getByText("Bengali")).toBeInTheDocument();
    expect(screen.getByText("Comfort")).toBeInTheDocument();
  });

  it("should separate main and side dishes with section headers", async () => {
    render(<RecipesPage />);
    await waitFor(() => {
      expect(screen.getByText("Sambar")).toBeInTheDocument();
    });
    // Section headers show count in parentheses
    expect(screen.getByText(/Main Dishes \(2\)/)).toBeInTheDocument();
    expect(screen.getByText(/Side Dishes \(1\)/)).toBeInTheDocument();
  });

  it("should show type toggle buttons", async () => {
    render(<RecipesPage />);
    await waitFor(() => {
      expect(screen.getByText("Sambar")).toBeInTheDocument();
    });
    // Type toggle has "Main Dishes" and "Side Dishes" as toggle button labels
    // These are separate from the section headers — check they exist as buttons
    const mainDishButtons = screen.getAllByText("Main Dishes");
    expect(mainDishButtons.length).toBeGreaterThanOrEqual(1);
    const sideDishButtons = screen.getAllByText("Side Dishes");
    expect(sideDishButtons.length).toBeGreaterThanOrEqual(1);
  });

  it("should display the page heading", async () => {
    render(<RecipesPage />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Recipes" })).toBeInTheDocument();
    });
  });
});
