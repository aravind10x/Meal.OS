/**
 * Tests for the Cook Brief page (Phase 1 + Phase 2 enhancements).
 *
 * Verifies: brief loading, display, copy button, voice note generation,
 * audio player, download, share, Hindi script display, TTS persistence.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CookBriefPage from "@/app/brief/[id]/page";
import { server } from "../mocks/handlers";
import { http, HttpResponse } from "msw";
import {
  MOCK_COOK_BRIEF,
  MOCK_VOICE_AUDIO,
  MOCK_VOICE_SCRIPT,
} from "../mocks/handlers";

vi.mock("next/navigation", () => ({
  usePathname: () => "/brief/1",
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useParams: () => ({ id: "1" }),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

describe("CookBriefPage", () => {
  it("should display the 'Cook Brief' title", () => {
    render(<CookBriefPage />);
    expect(screen.getByText("Cook Brief")).toBeInTheDocument();
    expect(screen.getByText("Share-ready handoff")).toBeInTheDocument();
  });

  it("should load and display the brief text", async () => {
    render(<CookBriefPage />);
    await waitFor(() => {
      expect(screen.getByText(/TODAY'S MENU/)).toBeInTheDocument();
    });
  });

  it("should display dish names in the brief", async () => {
    render(<CookBriefPage />);
    await waitFor(() => {
      expect(screen.getByText(/Sambar/)).toBeInTheDocument();
      expect(screen.getByText(/Beans Poriyal/)).toBeInTheDocument();
    });
  });

  it("should show a Copy Brief button", async () => {
    render(<CookBriefPage />);
    await waitFor(() => {
      expect(screen.getByText("Copy Brief")).toBeInTheDocument();
    });
  });

  it("should show a View Shopping List button", async () => {
    render(<CookBriefPage />);
    await waitFor(() => {
      expect(screen.getByText("View Shopping List")).toBeInTheDocument();
    });
  });

  it("should show the Hindi Voice Note section", async () => {
    render(<CookBriefPage />);
    await waitFor(() => {
      expect(screen.getByText("Hindi Voice Note")).toBeInTheDocument();
      expect(screen.getByText("Structured for WhatsApp or voice")).toBeInTheDocument();
    });
  });

  it("should show Generate Voice Note button initially", async () => {
    render(<CookBriefPage />);
    await waitFor(() => {
      expect(screen.getByText("Generate Voice Note")).toBeInTheDocument();
    });
  });

  it("should show audio player and actions after voice generation", async () => {
    const user = userEvent.setup();
    render(<CookBriefPage />);

    await waitFor(() => {
      expect(screen.getByText("Generate Voice Note")).toBeInTheDocument();
    });

    const genButton = screen.getByText("Generate Voice Note");
    await user.click(genButton);

    // After generation completes, should show player
    await waitFor(() => {
      expect(screen.getByText("Cook Brief Voice Note")).toBeInTheDocument();
    });

    // Should show download and share buttons
    expect(screen.getByText("Download")).toBeInTheDocument();
    expect(screen.getByText("Share WhatsApp")).toBeInTheDocument();
  });

  it("should show Hindi script toggle after voice generation", async () => {
    const user = userEvent.setup();
    render(<CookBriefPage />);

    await waitFor(() => {
      expect(screen.getByText("Generate Voice Note")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Generate Voice Note"));

    await waitFor(() => {
      expect(
        screen.getByText("Show Hindi script (for manual recording)")
      ).toBeInTheDocument();
    });
  });

  it("should expand and show Hindi script text when toggled", async () => {
    const user = userEvent.setup();
    render(<CookBriefPage />);

    await waitFor(() => {
      expect(screen.getByText("Generate Voice Note")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Generate Voice Note"));

    await waitFor(() => {
      expect(
        screen.getByText("Show Hindi script (for manual recording)")
      ).toBeInTheDocument();
    });

    // Click to expand the script
    await user.click(
      screen.getByText("Show Hindi script (for manual recording)")
    );

    await waitFor(() => {
      // Should show the Hindi script text
      expect(screen.getByText(/नमस्ते/)).toBeInTheDocument();
    });
  });

  it("should restore cached voice data from brief response on load", async () => {
    // Override the brief handler to include cached voice data
    const API_BASE = "http://localhost:8000";
    server.use(
      http.get(`${API_BASE}/api/brief/:planId`, () => {
        return HttpResponse.json({
          ...MOCK_COOK_BRIEF,
          voice_audio_url: MOCK_VOICE_AUDIO.audio_url,
          voice_script_text: MOCK_VOICE_SCRIPT.script_text,
        });
      })
    );

    render(<CookBriefPage />);

    // Should NOT show "Generate Voice Note" — audio player should appear directly
    await waitFor(() => {
      expect(screen.getByText("Cook Brief Voice Note")).toBeInTheDocument();
    });

    // Generate button should NOT be visible
    expect(screen.queryByText("Generate Voice Note")).not.toBeInTheDocument();

    // Audio action buttons should be visible
    expect(screen.getByText("Download")).toBeInTheDocument();
    expect(screen.getByText("Share WhatsApp")).toBeInTheDocument();
  });
});
