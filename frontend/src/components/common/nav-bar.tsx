"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  CalendarDays,
  ClipboardList,
  LayoutDashboard,
  UtensilsCrossed,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/home", label: "Dashboard", icon: LayoutDashboard },
  { href: "/recipes", label: "Recipes", icon: BookOpen },
  { href: "/checkin", label: "Plan", icon: CalendarDays },
  { href: "/history", label: "History", icon: ClipboardList },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary navigation"
      className="fixed inset-x-0 bottom-0 z-50 px-3 pb-3 safe-area-bottom md:top-0 md:bottom-auto md:px-6 md:pb-0"
    >
      <div className="mx-auto max-w-6xl">
        <div className="hidden items-center justify-between rounded-[1.75rem] border border-white/70 bg-white/78 px-3 py-3 shadow-[0_18px_50px_rgba(24,38,37,0.08)] backdrop-blur-xl md:flex">
          <Link href="/" className="flex items-center gap-3 pl-1">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
              <UtensilsCrossed className="h-5 w-5" />
            </div>
            <div>
              <p className="font-mono text-[0.72rem] uppercase tracking-[0.28em] text-muted-foreground">
                Meal.OS
              </p>
              <p className="text-sm font-semibold tracking-tight text-foreground">
                Household meal system
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="grid h-16 grid-cols-4 rounded-[1.75rem] border border-white/70 bg-white/88 px-2 shadow-[0_18px_40px_rgba(24,38,37,0.12)] backdrop-blur-xl md:hidden">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center gap-0.5 rounded-2xl px-3 py-1 transition-colors",
                  isActive
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <item.icon
                  className={cn("h-5 w-5", isActive && "stroke-[2.4]")}
                />
                <span className="text-[10px] font-semibold tracking-[0.04em]">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
