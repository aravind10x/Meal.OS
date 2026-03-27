/**
 * Tests for NavBar component.
 *
 * Verifies: navigation links presence, labels, href targets, and shell branding.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { NavBar } from "@/components/common/nav-bar";

// Mock Next.js navigation
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

describe("NavBar", () => {
  it("should render the Meal.OS brand label", () => {
    render(<NavBar />);
    expect(screen.getByText("Meal.OS")).toBeInTheDocument();
  });

  it("should render all navigation items", () => {
    render(<NavBar />);
    expect(screen.getAllByText("Home").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Recipes").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Plan").length).toBeGreaterThan(0);
    expect(screen.getAllByText("History").length).toBeGreaterThan(0);
  });

  it("should have correct link targets", () => {
    render(<NavBar />);
    const links = screen.getAllByRole("link");
    const hrefs = links.map((link) => link.getAttribute("href"));
    expect(hrefs).toContain("/");
    expect(hrefs).toContain("/recipes");
    expect(hrefs).toContain("/checkin");
    expect(hrefs).toContain("/history");
  });

  it("should preserve the 4 unique navigation destinations", () => {
    render(<NavBar />);
    const links = screen.getAllByRole("link");
    const uniqueHrefs = [...new Set(links.map((link) => link.getAttribute("href")))];
    expect(uniqueHrefs).toHaveLength(4);
  });
});
