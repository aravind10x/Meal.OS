import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Get a local date string in YYYY-MM-DD format.
 * Uses local timezone (not UTC) to avoid date drift.
 */
export function toLocalDateString(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Get tomorrow's date in YYYY-MM-DD using the local timezone.
 */
export function getTomorrowDate(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return toLocalDateString(d);
}
