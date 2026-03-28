/**
 * Tests for the Plan Review page.
 *
 * Verifies: loading plans, displaying candidates, approval flow,
 * swap dish interaction, curd rice toggle.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import PlansPage from "@/app/plans/page";
import { server, MOCK_APPROVED_PLAN } from "@/__tests__/mocks/handlers";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  usePathname: () => "/plans",
  useRouter: () => ({ push: mockPush, back: vi.fn() }),
  useSearchParams: () => ({
    get: (key: string) => (key === "date" ? "2026-02-16" : null),
  }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("PlansPage", () => {
  it("should display the 'Plans' title after loading", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getByText("Plans")).toBeInTheDocument();
    });
  });

  it("should display option tabs for multiple plans", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getByText("Option 1")).toBeInTheDocument();
      expect(screen.getByText("Option 2")).toBeInTheDocument();
      expect(screen.getByText("Option 3")).toBeInTheDocument();
    });
  });

  it("should prefer draft candidates over an older approved plan for the same date", async () => {
    server.use(
      http.get("http://localhost:8000/api/planner/approved", () => {
        return HttpResponse.json(MOCK_APPROVED_PLAN);
      })
    );

    render(<PlansPage />);

    await waitFor(() => {
      expect(screen.getByText("Plans")).toBeInTheDocument();
      expect(screen.getByText("Option 1")).toBeInTheDocument();
    });

    expect(screen.queryByText("Approved")).not.toBeInTheDocument();
  });

  it("should allow option card copy to wrap inside the tab trigger", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getAllByRole("tab")[0]).toHaveClass("whitespace-normal");
    });
  });

  it("should let the plan tablist grow to the height of the option cards", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getByRole("tablist")).toHaveClass(
        "group-data-[orientation=horizontal]/tabs:h-auto"
      );
      expect(screen.getByRole("tablist")).toHaveClass("items-stretch");
    });
  });

  it("should display the first plan's cuisine", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getAllByText("South Indian").length).toBeGreaterThan(0);
    });
  });

  it("should display dish names for the first plan", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getByText("Sambar")).toBeInTheDocument();
      expect(screen.getByText("Beans Poriyal")).toBeInTheDocument();
    });
  });

  it("should display the plan rationale", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(
        screen.getAllByText(
          /Classic South Indian meal, uses available beans and drumstick/
        ).length
      ).toBeGreaterThan(0);
    });
  });

  it("should display an 'Approve This Plan' button", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getByText("Approve This Plan")).toBeInTheDocument();
    });
  });

  it("should show approved state after clicking approve", async () => {
    render(<PlansPage />);

    await waitFor(() => {
      expect(screen.getByText("Approve This Plan")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Approve This Plan"));

    await waitFor(() => {
      expect(screen.getByText("Approved")).toBeInTheDocument();
    });
  });

  it("should show 'Open Cook Brief' button after approval", async () => {
    render(<PlansPage />);

    await waitFor(() => {
      fireEvent.click(screen.getByText("Approve This Plan"));
    });

    await waitFor(() => {
      expect(screen.getByText("Open Cook Brief")).toBeInTheDocument();
    });
  });

  it("should show 'Shopping' button after approval", async () => {
    render(<PlansPage />);

    await waitFor(() => {
      fireEvent.click(screen.getByText("Approve This Plan"));
    });

    await waitFor(() => {
      expect(screen.getByText("Shopping")).toBeInTheDocument();
    });
  });

  it("should display kid notes when present", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(
        screen.getByText(/Set aside dal before adding sambar masala/)
      ).toBeInTheDocument();
    });
  });

  // --- Swap Dish ---

  it("should show swap buttons on each dish", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getByLabelText("Swap Sambar")).toBeInTheDocument();
      expect(screen.getByLabelText("Swap Beans Poriyal")).toBeInTheDocument();
    });
  });

  it("should open swap sheet when a dish is tapped", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getByLabelText("Swap Sambar")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText("Swap Sambar"));

    await waitFor(() => {
      expect(screen.getByText("Swap Sambar")).toBeInTheDocument();
      // Should show swap alternatives
      expect(screen.getByText("Rasam")).toBeInTheDocument();
      expect(screen.getByText("Avial")).toBeInTheDocument();
      expect(screen.getByText("Palak Paneer")).toBeInTheDocument();
    });
  });

  // --- Curd Rice Toggle ---

  it("should display the curd rice toggle", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(
        screen.getByLabelText("Toggle optional curd rice side")
      ).toBeInTheDocument();
    });
  });

  it("should show the curd rice toggle text", async () => {
    render(<PlansPage />);
    await waitFor(() => {
      expect(screen.getByText("Optional curd rice side")).toBeInTheDocument();
    });
  });
});
