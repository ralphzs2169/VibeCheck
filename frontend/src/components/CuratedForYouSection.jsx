import React from "react";
import { SlidersHorizontal, MapPin } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { BASE_URL } from "../services/api";
import getVibeLevelFromScore from "../utils/vibeLabel";

function getThemeClasses(theme) {
  switch (theme) {
    case "emerald":
      return "bg-emerald-100 text-emerald-700";
    case "teal":
      return "bg-teal-100 text-teal-700";
    case "cyan":
      return "bg-cyan-100 text-cyan-700";
    case "amber":
      return "bg-amber-100 text-amber-700";
    case "orange":
      return "bg-orange-100 text-orange-700";
    case "red":
    case "crimson":
      return "bg-red-100 text-red-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

function formatReviews(n) {
  return `${Intl.NumberFormat().format(n)} verified reviews`;
}

export default function CuratedForYouSection({
  businesses = [],
  vibeDataMap = {},
  loading = false,
  error = null,
}) {
  const navigate = useNavigate();

  const topSix = [...businesses]
    .sort((a, b) => {
      const scoreA = vibeDataMap[a.id]?.overall_score ?? 0;
      const scoreB = vibeDataMap[b.id]?.overall_score ?? 0;
      return scoreB - scoreA;
    })
    .slice(0, 6);

  return (
    <section className="w-full bg-white py-14 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">

        {/* HEADER */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-10 gap-4">
          <div>
            <h2 className="font-bold text-3xl text-[#0F172A]">
              Curated for You
            </h2>
            <p className="text-slate-500 text-base mt-1">
              Based on your recent analytics and preference profile
            </p>
          </div>

          <button className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-300 text-[#0F172A] font-semibold bg-white hover:bg-slate-50 transition">
            <SlidersHorizontal className="w-4 h-4" />
            <span>Sort by Rank</span>
          </button>
        </div>

        {/* STATES */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div
                key={idx}
                className="rounded-3xl border border-slate-100 shadow-sm p-6 animate-pulse"
              >
                <div className="h-40 rounded-3xl bg-slate-100 mb-6" />
                <div className="h-5 bg-slate-100 rounded w-2/3 mb-3" />
                <div className="h-4 bg-slate-100 rounded w-1/2 mb-6" />
                <div className="border-t pt-6">
                  <div className="h-10 bg-slate-100 rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-red-100 bg-red-50 text-red-700 px-5 py-4">
            {error}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">

            {topSix.map((business) => {
              const score =
                vibeDataMap[business.id]?.overall_score ?? 0;

              const reviewCount =
                business?.review_count ??
                business?.reviews_count ??
                0;

              const vibe = getVibeLevelFromScore(score, reviewCount);

              return (
                <article
                  key={business.id}
                  onClick={() =>
                    navigate(`/business/${business.id}`)
                  }
                  className="bg-white border border-slate-100 shadow-sm hover:shadow-lg hover:-translate-y-1 transform-gpu transition-all overflow-hidden flex flex-col cursor-pointer group"
                >
                  
                  {/* IMAGE */}
                  <div className="overflow-hidden h-65">
                    {business.image_path ? (
                      <img
                        src={`${BASE_URL}${business.image_path}`}
                        alt={business.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full bg-slate-100" />
                    )}
                  </div>

                  {/* CONTENT */}
                  <div className="p-4 sm:p-5 flex flex-col flex-1">
                    <div className="flex justify-between items-center w-full mb-2.5 gap-2">
                      <h3 className="text-lg font-bold text-[#0F172A] truncate">
                        {business.name}
                      </h3>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${getThemeClasses(
                          vibe.theme
                        )}`}
                      >
                        {vibe.label}
                      </span>
                    </div>

                    {/* LOCATION */}
                    <div className="flex items-center gap-2 text-sm text-slate-500 mb-5 w-full">
                      <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span className="truncate">
                        {business.location || "Unknown location"}
                      </span>
                    </div>

                    {/* SCORE */}
                    <div className="pt-5 w-full mt-auto">
                      <div className="flex justify-between items-end w-full gap-3">
                        <div>
                          <p className="text-xs text-slate-400 uppercase tracking-widest mb-1">
                            Vibe Score
                          </p>
                          <p className="text-5xl font-bold text-[#0F172A] leading-none">
                            {score.toFixed(1)}
                          </p>
                        </div>

                        <div>
                          <p className="text-right text-xs text-slate-400 uppercase tracking-widest mb-1">
                            Reviews
                          </p>
                          <p className="text-right text-xs text-slate-700 font-medium">
                            {formatReviews(reviewCount)}
                          </p>
                        </div>
                      </div>
                    </div>

                  </div>
                </article>
              );
            })}

          </div>
        )}
      </div>
    </section>
  );
}