// Forex market is open Sun 5pm ET → Fri 5pm ET
export function isForexMarketOpen(now = new Date()): boolean {
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    weekday: "short",
    hour: "numeric",
    minute: "numeric",
    hour12: false,
  });

  const parts = Object.fromEntries(fmt.formatToParts(now).map((p) => [p.type, p.value]));
  const day = parts.weekday; // "Sun", "Mon", ..., "Sat"
  const hour = parseInt(parts.hour);
  const minute = parseInt(parts.minute);
  const minutesOfDay = hour * 60 + minute;
  const fivePm = 17 * 60;

  if (day === "Sat") return false;
  if (day === "Sun" && minutesOfDay < fivePm) return false;
  if (day === "Fri" && minutesOfDay >= fivePm) return false;
  return true;
}
