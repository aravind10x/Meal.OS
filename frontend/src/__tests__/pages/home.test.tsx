/**
 * Tests for the Home page.
 *
 * Verifies: Meal.OS branding baseline, product-story framing, and preview surfaces.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import HomePage from "@/app/page";

// Mock Next.js dependencies
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}));

describe("HomePage", () => {
  it("should display the Meal.OS title", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Meal.OS" })
    ).toBeInTheDocument();
  });

  it("should display the public product framing", () => {
    render(<HomePage />);
    expect(
      screen.getByText(
        "Tonight's 60-second check-in becomes tomorrow's cooking plan."
      )
    ).toBeInTheDocument();
  });

  it("should have a 'Plan Tomorrow's Meals' CTA", () => {
    render(<HomePage />);
    expect(screen.getByText("Plan Tomorrow's Meals")).toBeInTheDocument();
  });

  it("should have a 'Recipe Library' CTA", () => {
    render(<HomePage />);
    expect(screen.getByText("Recipe Library")).toBeInTheDocument();
  });

  it("should show the product output preview section", () => {
    render(<HomePage />);
    expect(screen.getByText("What Meal.OS Produces")).toBeInTheDocument();
    expect(screen.getByText("Plan Options")).toBeInTheDocument();
    expect(screen.getByText("Cook Brief")).toBeInTheDocument();
    expect(screen.getByText("Shopping Delta")).toBeInTheDocument();
  });

  it("should show the workflow explainer section", () => {
    render(<HomePage />);
    expect(screen.getByText("How The Household Runs Tomorrow")).toBeInTheDocument();
    expect(screen.getByText("Nightly check-in")).toBeInTheDocument();
    expect(screen.getByText("Compare plans")).toBeInTheDocument();
    expect(screen.getByText("Cook handoff")).toBeInTheDocument();
  });

  it("should link to the recipes page", () => {
    render(<HomePage />);
    const links = screen.getAllByRole("link");
    const hrefs = links.map((l) => l.getAttribute("href"));
    expect(hrefs).toContain("/recipes");
  });

  it("should link to the checkin page", () => {
    render(<HomePage />);
    const links = screen.getAllByRole("link");
    const hrefs = links.map((l) => l.getAttribute("href"));
    expect(hrefs).toContain("/checkin");
  });

  it("should show the system status panel", () => {
    render(<HomePage />);
    expect(screen.getByText("Tomorrow Morning")).toBeInTheDocument();
    expect(screen.getByText("Cook-ready outputs")).toBeInTheDocument();
  });
});
