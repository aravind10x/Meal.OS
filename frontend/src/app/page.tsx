import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  ChefHat,
  ClipboardList,
  ShoppingCart,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavBar } from "@/components/common/nav-bar";
import { Button } from "@/components/ui/button";

const WORKFLOW_STEPS: {
  number: string;
  title: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    number: "01",
    title: "Nightly check-in",
    description:
      "Capture leftovers, available vegetables, and what needs using soon before the household goes to bed.",
    icon: CalendarDays,
  },
  {
    number: "02",
    title: "Compare plans",
    description:
      "Review multiple AI-generated meal strategies with rationale, balance, and shopping impact in one place.",
    icon: Sparkles,
  },
  {
    number: "03",
    title: "Cook handoff",
    description:
      "Turn the approved plan into a cook brief, Hindi voice note, and shopping delta that can be acted on in the morning.",
    icon: ChefHat,
  },
];

const OUTPUT_PREVIEWS: {
  title: string;
  description: string;
  detail: string;
  icon: LucideIcon;
}[] = [
  {
    title: "Plan Options",
    description:
      "Three distinct meal directions grounded in vegetables, leftovers, and recent meal history.",
    detail: "Decision support, not just recipe search.",
    icon: Sparkles,
  },
  {
    title: "Cook Brief",
    description:
      "A structured handoff artifact with the menu, notes, and execution details ready to share.",
    detail: "Designed to be screenshot- and WhatsApp-ready.",
    icon: ClipboardList,
  },
  {
    title: "Shopping Delta",
    description:
      "Only the ingredients that are still missing, separated from likely-available and pantry items.",
    detail: "Keeps morning shopping focused and minimal.",
    icon: ShoppingCart,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen pb-24 md:pb-10">
      <div className="mx-auto max-w-6xl px-4 pb-12 pt-6 md:px-6 lg:px-8">
        <section className="rounded-[2.4rem] border border-white/70 bg-[linear-gradient(160deg,rgba(255,255,255,0.96),rgba(245,245,239,0.9))] px-6 py-8 shadow-[0_30px_80px_rgba(24,38,37,0.08)] md:px-10 md:py-12">
          <div className="max-w-3xl">
            <p className="font-mono text-[0.72rem] uppercase tracking-[0.28em] text-muted-foreground">
              AI household meal operating system
            </p>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-foreground md:text-5xl">
              Meal.OS
            </h1>
            <p className="mt-5 max-w-3xl text-2xl font-semibold leading-tight tracking-[-0.03em] text-foreground md:text-[3rem] md:leading-[1.02]">
              Tonight&apos;s 60-second check-in becomes tomorrow&apos;s cooking
              plan.
            </p>
            <p className="mt-5 max-w-2xl text-sm leading-6 text-muted-foreground md:text-base">
              Built for Indian households coordinating meals with a cook:
              compare AI-generated options, approve one, and hand off a brief
              plus shopping delta before morning.
            </p>
            <div className="mt-8">
              <Button asChild size="lg" className="h-12 rounded-full px-6">
                <Link href="/checkin">
                  Plan Tomorrow&apos;s Meals
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-[2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(247,246,241,0.92),rgba(255,255,255,0.84))] p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)] md:p-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                Inside Meal.OS
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                Plan comparison preview
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              One example of the artifact the household reviews before locking
              tomorrow&apos;s cooking plan.
            </p>
          </div>

          <div className="mt-6 rounded-[1.8rem] border border-border/80 bg-white/88 p-4 shadow-[0_12px_30px_rgba(24,38,37,0.06)] md:p-5">
            <div className="grid gap-3 lg:grid-cols-[minmax(0,1.05fr)_280px]">
              <div className="space-y-4">
                <div className="grid gap-2 md:grid-cols-3">
                  <PreviewOption
                    title="Option 1"
                    cuisine="South Indian"
                    detail="Uses drumstick and beans with a familiar weekday flow."
                    selected
                  />
                  <PreviewOption
                    title="Option 2"
                    cuisine="North Indian"
                    detail="Higher-protein direction with paneer and spinach."
                  />
                  <PreviewOption
                    title="Option 3"
                    cuisine="Bengali"
                    detail="Comfort-first plan with lighter shopping impact."
                  />
                </div>

                <div className="rounded-[1.5rem] border border-border/70 bg-[rgba(245,245,239,0.72)] p-4">
                  <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-muted-foreground">
                    Why this plan works
                  </p>
                  <p className="mt-3 text-sm leading-6 text-foreground">
                    Classic South Indian meal, uses available vegetables, avoids
                    repeating the previous two days, and keeps the morning handoff
                    simple.
                  </p>
                </div>
              </div>

              <aside className="rounded-[1.5rem] border border-border/80 bg-[rgba(244,244,239,0.74)] p-4">
                <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-muted-foreground">
                  Approval snapshot
                </p>
                <p className="mt-3 text-lg font-semibold tracking-tight text-foreground">
                  South Indian
                </p>
                <div className="mt-4 space-y-3 text-sm text-foreground">
                  <div className="flex items-center justify-between gap-3">
                    <span>Sambar</span>
                    <span className="text-xs text-muted-foreground">main</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span>Beans Poriyal</span>
                    <span className="text-xs text-muted-foreground">side</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span>Shopping delta</span>
                    <span className="text-xs text-muted-foreground">2 items</span>
                  </div>
                </div>
              </aside>
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-[2rem] border border-white/70 bg-white/75 p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                How The Household Runs Tomorrow
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                One calm flow from kitchen check-in to cook handoff.
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              The goal is to finish tomorrow&apos;s meal decisions while everyone
              still has a minute tonight.
            </p>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {WORKFLOW_STEPS.map((step) => (
              <article
                key={step.number}
                className="rounded-[1.6rem] border border-border/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.88),rgba(244,244,239,0.72))] p-5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[0.78rem] uppercase tracking-[0.24em] text-muted-foreground">
                    {step.number}
                  </span>
                  <step.icon className="h-4 w-4 text-primary" />
                </div>
                <h3 className="mt-4 text-lg font-semibold tracking-tight text-foreground">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {step.description}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-8 rounded-[2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(246,245,240,0.88),rgba(255,255,255,0.82))] p-6 shadow-[0_18px_48px_rgba(24,38,37,0.06)]">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="font-mono text-[0.72rem] uppercase tracking-[0.24em] text-muted-foreground">
                What Meal.OS Produces
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                Artifacts your household can actually use.
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              The strongest part of the system is what comes out the other side:
              concrete outputs that remove one more morning decision.
            </p>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {OUTPUT_PREVIEWS.map((item) => (
              <article
                key={item.title}
                className="rounded-[1.6rem] border border-border/80 bg-white/78 p-5"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-secondary text-primary">
                    <item.icon className="h-4 w-4" />
                  </div>
                  <h3 className="text-lg font-semibold tracking-tight text-foreground">
                    {item.title}
                  </h3>
                </div>
                <p className="mt-4 text-sm leading-6 text-muted-foreground">
                  {item.description}
                </p>
                <p className="mt-4 text-sm font-medium text-foreground">
                  {item.detail}
                </p>
              </article>
            ))}
          </div>
        </section>
      </div>

      <NavBar />
    </div>
  );
}

function PreviewOption({
  title,
  cuisine,
  detail,
  selected = false,
}: {
  title: string;
  cuisine: string;
  detail: string;
  selected?: boolean;
}) {
  return (
    <article
      className={
        selected
          ? "rounded-[1.35rem] border border-primary/30 bg-[rgba(238,248,245,0.86)] p-4 shadow-[0_10px_24px_rgba(24,38,37,0.06)]"
          : "rounded-[1.35rem] border border-border/80 bg-[rgba(248,248,245,0.82)] p-4"
      }
    >
      <div className="flex items-center justify-between gap-2">
        <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-muted-foreground">
          {title}
        </p>
        <span className="rounded-full bg-white/90 px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
          {cuisine}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-foreground">{detail}</p>
    </article>
  );
}
