import React, { useEffect, useState } from "react";
import {
  HeartPulse, ArrowUp, ArrowDown, Minus,
  ShieldCheck, Database, AlertCircle, TrendingUp,
  Activity, Zap,
} from "lucide-react";

/* ─────────────────────────────────────────
   CONSTANTS
───────────────────────────────────────── */
const BRAND = "#004687";

const HEALTH_CONFIG = {
  critical:  { bg: "bg-red-50",     border: "border-red-200",    text: "text-red-700",     bar: "bg-red-500",     glow: "#ef4444" },
  poor:      { bg: "bg-orange-50",  border: "border-orange-200", text: "text-orange-700",  bar: "bg-orange-500",  glow: "#f97316" },
  neutral:   { bg: "bg-slate-50",   border: "border-slate-200",  text: "text-slate-700",   bar: "bg-slate-400",   glow: "#94a3b8" },
  good:      { bg: "bg-emerald-50", border: "border-emerald-200",text: "text-emerald-700", bar: "bg-emerald-500", glow: "#22c55e" },
  excellent: { bg: "bg-green-50",   border: "border-green-200",  text: "text-green-700",   bar: "bg-green-500",   glow: "#16a34a" },
};

/* ─────────────────────────────────────────
   SUB-COMPONENTS
───────────────────────────────────────── */
const SeverityDot = ({ severity = "low" }) => {
  const map = { high: "bg-red-500", medium: "bg-orange-400", low: "bg-yellow-400" };
  return <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 mt-0.5 ${map[severity] || "bg-gray-300"}`} />;
};

function AnimatedBar({ pct, color, delay = 0 }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(pct), 120 + delay);
    return () => clearTimeout(t);
  }, [pct, delay]);
  return (
    <div className="h-1 w-full bg-gray-100 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

function KPICard({ icon: Icon, label, value, sub, accent, barPct, barColor, delay }) {
  return (
    <div className="relative bg-white border border-gray-100 rounded-2xl p-4 overflow-hidden group hover:shadow-md transition-shadow duration-200">
      {/* top accent line */}
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl" style={{ backgroundColor: accent }} />

      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{label}</p>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${accent}14` }}>
          <Icon className="w-3.5 h-3.5" style={{ color: accent }} />
        </div>
      </div>

      <p className="text-2xl font-bold text-gray-900 leading-none mb-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1 leading-snug">{sub}</p>}

      {barPct != null && (
        <div className="mt-3">
          <AnimatedBar pct={barPct} color={barColor} delay={delay} />
        </div>
      )}
    </div>
  );
}

const Skeleton = () => (
  <div className="animate-pulse bg-white border border-gray-100 rounded-2xl p-6">
    <div className="h-5 w-40 bg-gray-200 rounded mb-2" />
    <div className="h-4 w-64 bg-gray-100 rounded mb-6" />
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-gray-100 rounded-xl p-4 space-y-2">
          <div className="h-3 w-1/2 bg-gray-200 rounded" />
          <div className="h-7 w-3/4 bg-gray-200 rounded" />
          <div className="h-1 w-full bg-gray-200 rounded-full" />
        </div>
      ))}
    </div>
  </div>
);

/* ─────────────────────────────────────────
   MAIN
───────────────────────────────────────── */
export default function ExecutiveSummary({ dashboard = {}, loading = false }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { const t = setTimeout(() => setMounted(true), 60); return () => clearTimeout(t); }, []);

  if (loading) return <Skeleton />;

  /* — data extraction — */
  const profileName  = dashboard?.profile?.name ?? "Business";
  const bh           = dashboard.business_health ?? {};
  const healthLabel  = bh.label ?? bh?.insights?.health?.label ?? "Unknown";
  const healthMeaning= bh?.insights?.health?.meaning ?? "";
  const healthLevel  = (bh?.insights?.health?.level || "neutral").toLowerCase();
  const reviewCount  = Number(dashboard.review_count ?? 0);
  const vibeTrend    = dashboard.vibe_score_trend?.trend ?? dashboard.vibe_score_trend ?? "stable";
  const trendReliable= Boolean(dashboard.vibe_score_trend?.meta?.is_reliable);
  const sentimentVol = dashboard.sentiment_volatility ?? {};
  const vibeVol      = dashboard.vibe_volatility ?? {};
  const bothReliable = [sentimentVol, vibeVol].every(x => Boolean(x?.meta?.is_reliable));
  const insufficientData = reviewCount < 3 || !bothReliable;

  /* — cold start — */
  if (insufficientData) {
    return (
      <div className="bg-white border border-gray-100 rounded-2xl p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Executive Summary</h3>
            <p className="text-sm text-gray-400">{profileName} · High-level performance snapshot</p>
          </div>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-500 border border-slate-200">
            Pending Data
          </span>
        </div>
        <div className="flex flex-col items-center justify-center py-10 gap-3">
          <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: `${BRAND}12` }}>
            <Activity className="w-5 h-5" style={{ color: BRAND }} />
          </div>
          <p className="text-gray-700 font-medium text-sm">Not enough data yet</p>
          <p className="text-gray-400 text-xs text-center max-w-xs">
            Collect at least 3 reviews to unlock your Executive Summary and business health insights.
          </p>
          <div className="mt-2 w-48">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{reviewCount} reviews</span>
              <span>3 needed</span>
            </div>
            <AnimatedBar pct={Math.min((reviewCount / 3) * 100, 100)} color="bg-[#004687]" delay={200} />
          </div>
        </div>
      </div>
    );
  }

  /* — computed values — */
  const healthCfg   = HEALTH_CONFIG[healthLevel] ?? HEALTH_CONFIG.neutral;
  const healthScoreRaw = bh?.score ?? bh?.value ?? null;
  const healthScoreNum = typeof healthScoreRaw === "number" && healthScoreRaw <= 1
    ? Math.round(healthScoreRaw * 100)
    : typeof healthScoreRaw === "number" ? healthScoreRaw : null;
  const healthScoreStr = healthScoreNum != null ? `${healthScoreNum}` : "—";

  let reliabilityLabel = "Reliable";
  let reliabilityColor = "#22c55e";
  if (bh?.insights?.confidence?.level === "weak" || reviewCount < 10) { reliabilityLabel = "Early Data"; reliabilityColor = "#f97316"; }
  if (bh?.insights?.confidence?.level === "low") { reliabilityLabel = "Low"; reliabilityColor = "#ef4444"; }

  const stability = (() => {
    const s1 = sentimentVol?.stability ?? "unknown";
    const s2 = vibeVol?.stability ?? "unknown";
    if (s1 === "stable"   && s2 === "stable")   return { label: "Experience is consistent",        detail: [sentimentVol.interpretation, vibeVol.interpretation] };
    if (s1 === "unstable" && s2 === "unstable") return { label: "Performance is fluctuating",       detail: [sentimentVol.interpretation, vibeVol.interpretation] };
    if (s1 === "mixed"    || s2 === "mixed")    return { label: "Some inconsistencies detected",    detail: [sentimentVol.interpretation, vibeVol.interpretation] };
    return { label: "Insufficient stability data", detail: [] };
  })();

  const signals  = (dashboard.negative_signals?.signals ?? dashboard.negative_signals ?? []).slice(0, 3);
  const sampleSize = Math.max(Number(sentimentVol?.meta?.sample_size ?? 0), Number(vibeVol?.meta?.sample_size ?? 0));

  const trendIcon = vibeTrend === "improving"
    ? <ArrowUp   className="w-4 h-4 text-emerald-500" />
    : vibeTrend === "declining"
    ? <ArrowDown className="w-4 h-4 text-red-500" />
    : <Minus     className="w-4 h-4 text-gray-400" />;

  const trendColor = vibeTrend === "improving" ? "#22c55e" : vibeTrend === "declining" ? "#ef4444" : "#94a3b8";

  /* — narrative — */
  const parts = [];
  if (healthLabel) parts.push(`Health is ${healthLabel}`);
  if (vibeTrend)   parts.push(`trend is ${vibeTrend}`);
  if (stability?.label) parts.push(stability.label.toLowerCase());
  if (signals.length) parts.push(`${signals.length} negative signal${signals.length > 1 ? "s" : ""} flagged`);
  const narrative = parts.length ? parts.join(" · ") + "." : "No immediate concerns detected.";

  /* ─────── RENDER ─────── */
  return (
    <div
      className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm"
      style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.3s ease" }}
    >
      {/* ── Header bar ── */}
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between"
           style={{ background: `linear-gradient(135deg, ${BRAND}08 0%, transparent 100%)` }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: BRAND }}>
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 leading-none">Executive Summary</h3>
            <p className="text-xs text-gray-400 mt-0.5">{profileName}</p>
          </div>
        </div>

        <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-full border ${healthCfg.bg} ${healthCfg.border} ${healthCfg.text}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${healthCfg.bar}`} />
          {healthLabel}
        </span>
      </div>

      <div className="p-6 space-y-5">

        {/* ── KPI cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KPICard
            icon={HeartPulse}
            label="Health Score"
            value={healthScoreStr}
            sub={healthMeaning || "Composite performance"}
            accent={healthCfg.glow}
            barPct={healthScoreNum}
            barColor={healthCfg.bar}
            delay={0}
          />
          <KPICard
            icon={Database}
            label="Total Reviews"
            value={reviewCount}
            sub="Customer responses analyzed"
            accent={BRAND}
            barPct={Math.min((reviewCount / 50) * 100, 100)}
            barColor="bg-[#004687]"
            delay={80}
          />
          <KPICard
            icon={TrendingUp}
            label="Trend Direction"
            value={<span className="flex items-center gap-1.5 capitalize">{vibeTrend} {trendIcon}</span>}
            sub={trendReliable ? "Reliable signal" : "Limited samples"}
            accent={trendColor}
            delay={160}
          />
          <KPICard
            icon={ShieldCheck}
            label="Data Reliability"
            value={reliabilityLabel}
            sub="Based on signal confidence"
            accent={reliabilityColor}
            delay={240}
          />
        </div>

        {/* ── Stability + Signals ── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">

          {/* Stability */}
          <div className="lg:col-span-3 rounded-2xl border border-gray-100 bg-gray-50 p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${BRAND}14` }}>
                <Activity className="w-3.5 h-3.5" style={{ color: BRAND }} />
              </div>
              <p className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Stability</p>
            </div>
            <p className="text-sm font-semibold text-gray-900 mb-2">{stability.label}</p>
            <div className="space-y-1">
              {stability.detail.filter(Boolean).map((d, i) => (
                <p key={i} className="text-xs text-gray-500 leading-relaxed">{d}</p>
              ))}
            </div>
          </div>

          {/* Negative signals */}
          <div className="lg:col-span-2 rounded-2xl border border-gray-100 bg-gray-50 p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-lg bg-red-50 flex items-center justify-center">
                <AlertCircle className="w-3.5 h-3.5 text-red-500" />
              </div>
              <p className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Negative Signals</p>
            </div>
            {signals.length ? (
              <div className="space-y-2">
                {signals.map((s, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-gray-700">
                    <SeverityDot severity={(s.severity || "low").toLowerCase()} />
                    <span className="leading-relaxed">{s.text ?? s.message ?? "—"}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-emerald-600">
                <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
                No active negative signals
              </div>
            )}
          </div>
        </div>

        {/* ── Insight strip ── */}
        <div
          className="rounded-2xl p-4 flex items-start gap-3"
          style={{ background: `linear-gradient(135deg, ${BRAND}0d 0%, ${BRAND}05 100%)`, border: `1px solid ${BRAND}20` }}
        >
          <div className="w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ backgroundColor: BRAND }}>
            <Zap className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold mb-1" style={{ color: BRAND }}>AI Insight</p>
            <p className="text-sm text-gray-800 leading-relaxed capitalize">{narrative}</p>
          </div>
          <p className="text-xs text-gray-400 flex-shrink-0 mt-0.5">
            {sampleSize > 0 ? `${sampleSize} pts` : "—"}
          </p>
        </div>

      </div>
    </div>
  );
}