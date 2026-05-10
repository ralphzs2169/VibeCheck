import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus, Zap, ShieldCheck, BarChart2, Activity } from "lucide-react";

const BRAND = "#004687";

function AnimatedBar({ pct, colorClass = "bg-[#004687]" }) {
  // Render a static bar (no entrance animation)
  const width = Math.max(0, Math.min(100, pct || 0));
  return (
    <div className="h-1 w-full bg-gray-100 rounded-full overflow-hidden">
      <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${width}%` }} />
    </div>
  );
}

/* ── human-friendly translations ── */
function humanVolatility(stability, volatility) {
  if (stability === "stable")   return { label: "Stable",  sub: "Vibe is steady over time",        color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-100" };
  if (stability === "unstable") return { label: "Unstable", sub: "Vibe is fluctuating over time",   color: "text-amber-600",   bg: "bg-amber-50",   border: "border-amber-100"   };
  return                               { label: "Mixed",    sub: "Some variation in vibe over time", color: "text-slate-600",   bg: "bg-slate-50",   border: "border-slate-100"   };
}

function humanTrend(trendLabel) {
  if (trendLabel === "improving") return { label: "Improving",  sub: "Customers are responding more positively", color: "text-emerald-600", icon: TrendingUp,   iconColor: "text-emerald-500" };
  if (trendLabel === "declining") return { label: "Declining",  sub: "Satisfaction has been dropping",           color: "text-red-600",     icon: TrendingDown, iconColor: "text-red-500"     };
  return                                 { label: "Holding Steady", sub: "No significant change recently",       color: "text-slate-600",   icon: Minus,        iconColor: "text-slate-400"   };
}

function humanDataQuality(quality) {
  if (quality === "high")     return { label: "Strong",   sub: "Insights are well-supported",   color: "text-emerald-600", pct: 90 };
  if (quality === "moderate") return { label: "Moderate", sub: "Enough data to act on",          color: "text-amber-600",   pct: 55 };
  if (quality === "low")      return { label: "Limited",  sub: "More reviews will improve this", color: "text-red-500",     pct: 25 };
  return                             { label: "Unknown",  sub: "Data quality unavailable",       color: "text-slate-400",   pct: 0  };
}

function humanColdStart(isColdStart) {
  return isColdStart
    ? { label: "Building History", sub: "Not enough history yet",       color: "text-amber-600",   bg: "bg-amber-50",   border: "border-amber-100"   }
    : { label: "Established",      sub: "Sufficient history to analyse", color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-100" };
}

/* ── tile ── */
function ContextTile({ icon: Icon, iconColor, label, value, valueColor, sub, bottom }) {
  return (
    <div className="bg-white border border-gray-100 shadow-sm rounded-2xl p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-gray-400">{label}</span>
        <div className="w-7 h-7 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${BRAND}12` }}>
          <Icon className={`w-3.5 h-3.5 ${iconColor}`} style={iconColor ? {} : { color: BRAND }} />
        </div>
      </div>
      <div>
        <p className={`text-xl font-bold leading-none ${valueColor}`}>{value}</p>
        <p className="text-xs text-gray-400 mt-1.5 leading-snug">{sub}</p>
      </div>
      {bottom && <div className="mt-auto pt-1">{bottom}</div>}
    </div>
  );
}

const Skeleton = () => (
  <div className="animate-pulse bg-white border border-gray-100 rounded-2xl p-6 space-y-4">
    <div className="h-4 w-32 bg-gray-200 rounded" />
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-gray-100 rounded-2xl p-4 space-y-2">
          <div className="h-3 w-1/2 bg-gray-200 rounded" />
          <div className="h-6 w-3/4 bg-gray-200 rounded" />
          <div className="h-1 w-full bg-gray-200 rounded-full" />
        </div>
      ))}
    </div>
  </div>
);

/* ── main ── */
export default function ExecutiveSummary({ dashboard = {}, loading = false }) {

  if (loading) return <Skeleton />;

  const bh           = dashboard.business_health ?? {};
  const bhRaw        = bh.raw ?? {};
  const sentimentVol = dashboard.sentiment_volatility ?? {};
  const vibeVol      = dashboard.vibe_volatility ?? {};
  const reviewCount  = Number(dashboard.review_count ?? 0);

  const hasEnoughData = (metric) => {
    const meta = metric?.meta;
    if (!meta) return true; // assume enough if no meta present
    const sample = Number(meta.sample_size ?? 0);
    const minReq = Number(meta.min_required ?? 0);
    return sample >= minReq;
  };

  /* ── derived values ── */
  const trendLabel   = bhRaw.trend_label ?? "stable";
  const trend        = humanTrend(trendLabel);
  const TrendIcon    = trend.icon;

  const vol          = humanVolatility(vibeVol.stability ?? sentimentVol.stability, vibeVol.volatility ?? sentimentVol.volatility);
  const dq           = humanDataQuality(bhRaw.data_quality);
  const cs           = humanColdStart(bhRaw.is_cold_start);

  return (
    <div className="space-y-3">

      {/* section label */}


      {/* 4 tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">

        {/* 1 — Data quality */}
        <ContextTile
          icon={BarChart2}
          label="Signal Strength"
          value={dq.label}
          valueColor={dq.color}
          sub={dq.sub}
          bottom={<AnimatedBar pct={dq.pct} colorClass="bg-[#004687]" delay={0} />}
          delay={80}
        />

        {/* 2 — Temporal vibe stability */}
        <ContextTile
          icon={Zap}
          label="Review Consistency"
          value={vol.label}
          valueColor={vol.color}
          sub={vol.sub}
          delay={160}
        />

        {/* 3 — Trend direction */}
        <ContextTile
          icon={TrendIcon}
          iconColor={trend.iconColor}
          label="Vibe Trend Direction"
          value={trend.label}
          valueColor={trend.color}
          sub={trend.sub}
          delay={240}
        />

        {/* 4 — Cold start */}
        <ContextTile
          icon={ShieldCheck}
          label="Data Maturity"
          value={cs.label}
          valueColor={cs.color}
          sub={cs.sub}
          delay={320}
        />

      </div>
    </div>
  );
}