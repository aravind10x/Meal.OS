/**
 * Tests for the Shopping List page.
 *
 * Verifies: loading items, categorized display, copy button.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import ShoppingListPage from "@/app/shopping/[id]/page";

vi.mock("next/navigation", () => ({
  usePathname: () => "/shopping/1",
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useParams: () => ({ id: "1" }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("ShoppingListPage", () => {
  it("should display the 'Shopping List' title", () => {
    render(<ShoppingListPage />);
    expect(screen.getByText("Shopping List")).toBeInTheDocument();
  });

  it("should load and display items by category", async () => {
    render(<ShoppingListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Need to Buy/)).toBeInTheDocument();
      expect(screen.getByText("Drumstick")).toBeInTheDocument();
    });
  });

  it("should show 'likely available' items", async () => {
    render(<ShoppingListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Likely Available/)).toBeInTheDocument();
      expect(screen.getByText("French Beans")).toBeInTheDocument();
    });
  });

  it("should show pantry staples", async () => {
    render(<ShoppingListPage />);
    await waitFor(() => {
      expect(screen.getByText(/Pantry Staples/)).toBeInTheDocument();
      expect(screen.getByText("Toor Dal")).toBeInTheDocument();
    });
  });

  it("should show item quantities", async () => {
    render(<ShoppingListPage />);
    await waitFor(() => {
      expect(screen.getByText(/200g/)).toBeInTheDocument();
    });
  });

  it("should show which dish each item is for", async () => {
    render(<ShoppingListPage />);
    await waitFor(() => {
      const matches = screen.getAllByText(/for Sambar/);
      expect(matches.length).toBeGreaterThan(0);
    });
  });

  it("should show a copy button", async () => {
    render(<ShoppingListPage />);
    await waitFor(() => {
      expect(screen.getByText("Copy Shopping List")).toBeInTheDocument();
    });
  });
});
