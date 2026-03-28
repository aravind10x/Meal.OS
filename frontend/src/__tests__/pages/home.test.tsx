/**
 * Tests for the landing page.
 *
 * Verifies: Meal.OS public framing, single-CTA hero, and artifact-led proof.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import HomePage from "@/app/page";

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
  it("shows the public Meal.OS promise", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { level: 1, name: "Meal.OS" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Tonight's 60-second check-in becomes tomorrow's cooking plan."
      )
    ).toBeInTheDocument();
  });

  it("keeps one primary planning CTA in the hero", () => {
    render(<HomePage />);
    expect(screen.getByText("Plan Tomorrow's Meals")).toBeInTheDocument();
    expect(screen.queryByText("Browse the recipe library")).not.toBeInTheDocument();
  });

  it("does not show the dashboard approval surface on the landing page", () => {
    render(<HomePage />);
    expect(screen.queryByText("Tomorrow's plan is approved")).not.toBeInTheDocument();
    expect(screen.queryByText("Tomorrow Morning")).not.toBeInTheDocument();
  });

  it("shows the product output preview section", () => {
    render(<HomePage />);
    expect(screen.getByText("What Meal.OS Produces")).toBeInTheDocument();
    expect(screen.getByText("Plan Options")).toBeInTheDocument();
    expect(screen.getByText("Cook Brief")).toBeInTheDocument();
    expect(screen.getByText("Shopping Delta")).toBeInTheDocument();
  });

  it("shows the workflow explainer section", () => {
    render(<HomePage />);
    expect(screen.getByText("How The Household Runs Tomorrow")).toBeInTheDocument();
    expect(screen.getByText("Nightly check-in")).toBeInTheDocument();
    expect(screen.getByText("Compare plans")).toBeInTheDocument();
    expect(screen.getByText("Cook handoff")).toBeInTheDocument();
  });

  it("shows a screenshot-style artifact preview section", () => {
    render(<HomePage />);
    expect(screen.getByText("Inside Meal.OS")).toBeInTheDocument();
    expect(screen.getByText("Plan comparison preview")).toBeInTheDocument();
  });

  it("links to the planning and dashboard routes", () => {
    render(<HomePage />);
    const links = screen.getAllByRole("link");
    const hrefs = links.map((link) => link.getAttribute("href"));
    expect(hrefs).toContain("/checkin");
    expect(hrefs).toContain("/home");
  });
});
