import { useState, useEffect } from 'react';
import HeroSection from '../components/HeroSection';
import SearchBar from '../components/SearchBar';
import InsightCard from '../components/InsightCard';
import ResortGrid from '../components/ResortGrid';
import FiltersBar from '../components/FiltersBar';
import Footer from '../components/Footer';
import axios from 'axios';

export default function Home() {
  const [resorts, setResorts] = useState([]);
  const [filteredResorts, setFilteredResorts] = useState([]);
  const [vibeDataMap, setVibeDataMap] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [sortBy, setSortBy] = useState('vibe-score-high');

  // Fetch all resorts with vibe data
  useEffect(() => {
    const fetchResorts = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('/api/homepage');
        
        // Handle response structure - could be array directly or wrapped in businesses property
        const businesses = Array.isArray(response.data) 
          ? response.data 
          : (Array.isArray(response.data.businesses) ? response.data.businesses : []);
        
        console.log('Fetched businesses:', businesses);
        setResorts(businesses);

        // Build vibe data map from the response
        const vibeMap = {};
        businesses.forEach((resort) => {
          if (resort.latest_vibe) {
            const vibe = resort.latest_vibe;
            const total = vibe.positive_count + vibe.mixed_count + vibe.negative_count;
            vibeMap[resort.id] = {
              overall_score: vibe.vibe_score,
              sentiment_distribution: {
                positive: total > 0 ? vibe.positive_count / total : 0.33,
                neutral: total > 0 ? vibe.mixed_count / total : 0.33,
                negative: total > 0 ? vibe.negative_count / total : 0.34,
              },
              summary: vibe.summary_text || 'Guest experiences analyzed',
            };
          } else {
            // Default vibe data if no snapshot exists
            vibeMap[resort.id] = {
              overall_score: 0.5,
              sentiment_distribution: {
                positive: 0.33,
                neutral: 0.33,
                negative: 0.34,
              },
              summary: 'Analyzing guest experiences...',
            };
          }
        });

        setVibeDataMap(vibeMap);
        setError(null);
      } catch (err) {
        setError('Failed to load resorts. Please try again.');
        console.error('Error fetching resorts:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResorts();
  }, []);

  // Filter and sort resorts
  useEffect(() => {
    let filtered = resorts.filter((resort) => {
      const matchesSearch = resort.name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const matchesLocation =
        !locationFilter ||
        (resort.location &&
          resort.location.toLowerCase().includes(locationFilter.toLowerCase()));
      return matchesSearch && matchesLocation;
    });

    // Sort resorts
    filtered.sort((a, b) => {
      const scoreA = vibeDataMap[a.id]?.overall_score || 0.5;
      const scoreB = vibeDataMap[b.id]?.overall_score || 0.5;
      const reviewsA = a.reviews_count || 0;
      const reviewsB = b.reviews_count || 0;

      switch (sortBy) {
        case 'vibe-score-high':
          return scoreB - scoreA;
        case 'vibe-score-low':
          return scoreA - scoreB;
        case 'most-reviewed':
          return reviewsB - reviewsA;
        case 'trending':
          // Would need trend data from API
          return scoreB - scoreA;
        case 'newest':
          return b.id - a.id;
        default:
          return 0;
      }
    });

    setFilteredResorts(filtered);
  }, [searchTerm, locationFilter, sortBy, resorts, vibeDataMap]);

  // Calculate insights
  const calculateInsights = () => {
    if (resorts.length === 0) {
      return {
        mostPositive: [],
        mostControversial: [],
        rising: [],
      };
    }

    // Most Positive (highest overall scores)
    const mostPositive = [...resorts]
      .sort(
        (a, b) =>
          (vibeDataMap[b.id]?.overall_score || 0) -
          (vibeDataMap[a.id]?.overall_score || 0)
      )
      .slice(0, 3)
      .map((r) => ({
        name: r.name,
        score: vibeDataMap[r.id]?.overall_score || 0.5,
      }));

    // Most Controversial (highest sentiment volatility - mix of positive and negative)
    const mostControversial = [...resorts]
      .map((resort) => {
        const dist = vibeDataMap[resort.id]?.sentiment_distribution || {
          positive: 0.33,
          neutral: 0.33,
          negative: 0.34,
        };
        const controversy = Math.abs(dist.positive - dist.negative);
        return {
          resort,
          controversy,
          score: vibeDataMap[resort.id]?.overall_score || 0.5,
        };
      })
      .sort((a, b) => b.controversy - a.controversy)
      .slice(0, 3)
      .map((item) => ({
        name: item.resort.name,
        score: item.score,
      }));

    // Rising (would need trend data, for now using variety)
    const rising = [...resorts]
      .sort(
        (a, b) =>
          (vibeDataMap[b.id]?.overall_score || 0) -
          (vibeDataMap[a.id]?.overall_score || 0)
      )
      .slice(3, 6)
      .map((r) => ({
        name: r.name,
        score: vibeDataMap[r.id]?.overall_score || 0.5,
      }));

    return {
      mostPositive,
      mostControversial,
      rising,
    };
  };

  const insights = calculateInsights();

  return (
    <div className="bg-white min-h-screen">
      {/* Hero Section with Search */}
      <HeroSection>
        <SearchBar onSearch={setSearchTerm} onLocationFilter={setLocationFilter} />
      </HeroSection>

      {/* Main Content */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          {/* Featured Insights */}
          <div className="mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-8">Key Insights Today</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <InsightCard
                icon="🔥"
                title="Most Positive Today"
                subtitle="Highest guest satisfaction"
                resorts={insights.mostPositive}
                type="positive"
              />
              <InsightCard
                icon="⚖️"
                title="Most Controversial"
                subtitle="Highly mixed reviews"
                resorts={insights.mostControversial}
                type="controversial"
              />
              <InsightCard
                icon="📈"
                title="Rising Resort"
                subtitle="Gaining engagement"
                resorts={insights.rising}
                type="rising"
              />
            </div>
          </div>

          {/* Filters and Sorting */}
          <div className="mb-8">
            <FiltersBar sortBy={sortBy} onSortChange={setSortBy} />
          </div>

          {/* Resort Grid */}
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-8">
              Discover Resorts ({filteredResorts.length})
            </h2>
            <ResortGrid
              resorts={filteredResorts}
              vibeDataMap={vibeDataMap}
              isLoading={isLoading}
              error={error}
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}
