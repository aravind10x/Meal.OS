/**
 * Tests for the dashboard page.
 *
 * Verifies: tasteful empty state, progressive action hierarchy,
 * and operational tomorrow-state handling.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import DashboardPage from "@/app/home/page";
import {
  MOCK_APPROVED_PLAN,
  MOCK_PLAN_CANDIDATE,
} from "@/__tests__/mocks/handlers";

const mockApproved = vi.fn();
const mockCandidates = vi.fn();
const mockHistory = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    planner: {
      approved: (...args: unknown[]) => mockApproved(...args),
      candidates: (...args: unknown[]) => mockCandidates(...args),
      history: (...args: unknown[]) => mockHistory(...args),
    },
  },
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/home",
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
}));

describe("DashboardPage", () => {
  beforeEach(() => {
    mockApproved.mockReset();
    mockCandidates.mockReset();
    mockHistory.mockReset();
    mockApproved.mockResolvedValue(null);
    mockCandidates.mockResolvedValue([]);
    mockHistory.mockResolvedValue([]);
  });

  it("shows a quiet empty state when there is no approved plan or draft plan", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Capture leftovers and what needs using soon, then generate tomorrow's plan."
        )
      ).toBeInTheDocument();
      expect(screen.getByText("Start Check-in")).toBeInTheDocument();
    });

    expect(screen.queryByText("Shopping")).not.toBeInTheDocument();
  });

  it("shows approved-plan actions without a separate next-action box", async () => {
    mockApproved.mockResolvedValue(MOCK_APPROVED_PLAN);

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Plan approved")).toBeInTheDocument();
      expect(screen.getByText("Open Cook Brief")).toBeInTheDocument();
    });

    expect(screen.getByText("Shopping")).toBeInTheDocument();
    expect(screen.getByText("View Plan")).toBeInTheDocument();
    expect(screen.queryByText("Next action")).not.toBeInTheDocument();
    expect(screen.queryByText("Tomorrow is set")).not.toBeInTheDocument();
  });

  it("shows review as the primary action when draft plans are ready", async () => {
    mockCandidates.mockResolvedValue([MOCK_PLAN_CANDIDATE]);

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Plan options ready")).toBeInTheDocument();
      expect(screen.getByText("Review options")).toBeInTheDocument();
    });

    expect(screen.queryByText("Open Cook Brief")).not.toBeInTheDocument();
    expect(screen.queryByText("Shopping")).not.toBeInTheDocument();
    expect(screen.queryByText("Next action")).not.toBeInTheDocument();
  });

  it("formats recent meal names instead of showing recipe ids", async () => {
    mockHistory.mockResolvedValue([
      {
        id: 1,
        history_date: "2026-02-15",
        meal_plan_id: null,
        dishes_cooked: ["palak_paneer", "aloo_gobi"],
        egg_style: "boiled",
        cuisine: "North Indian",
        notes: "",
        created_at: "2026-02-15T10:00:00Z",
      },
    ]);

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Palak Paneer, Aloo Gobi")).toBeInTheDocument();
    });

    expect(screen.queryByText("palak_paneer, aloo_gobi")).not.toBeInTheDocument();
  });
});
