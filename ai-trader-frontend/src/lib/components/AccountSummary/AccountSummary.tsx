import Link from "next/link";
import styles from "./AccountSummary.module.css";

async function getAccount() {
  try {
    const apiKey = process.env.OANDA_API_KEY;
    const accountId = process.env.OANDA_ACCOUNT_ID;
    const baseUrl = process.env.OANDA_BASE_URL;

    if (!apiKey || !accountId || !baseUrl) return null;

    const res = await fetch(`${baseUrl}/v3/accounts/${accountId}/summary`, {
      headers: { Authorization: `Bearer ${apiKey}` },
      cache: "no-store",
    });

    if (!res.ok) return null;

    const { account } = await res.json();
    return {
      balance: parseFloat(account.balance),
      nav: parseFloat(account.NAV),
      unrealizedPl: parseFloat(account.unrealizedPL),
      currency: account.currency,
    };
  } catch {
    return null;
  }
}

export default async function AccountSummary() {
  const account = await getAccount();

  const nav = account?.nav ?? 0;
  const unrealizedPl = account?.unrealizedPl ?? 0;
  const isPositive = unrealizedPl >= 0;

  return (
    <section className={styles.container}>
      <div>
        <p className={styles.label}>Account Balance</p>
        <h1 className={styles.balance}>
          ${nav.toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </h1>
        <p className={`${styles.profit} ${isPositive ? styles.positive : styles.negative}`}>
          {isPositive ? "+" : "-"}${Math.abs(unrealizedPl).toFixed(2)} unrealized
        </p>
      </div>
      <Link href="/trades" className={styles.tradesButton}>
        View all trades →
      </Link>
    </section>
  );
}
