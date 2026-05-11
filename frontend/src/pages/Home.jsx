import { useState, useEffect } from 'react';
import HeroSection from '../components/HeroSection';
import SearchBar from '../components/SearchBar';
import InsightCard from '../components/InsightCard';
import BusinessGrid from '../components/BusinessGrid';
import FiltersBar from '../components/FiltersBar';
import Footer from '../components/Footer';
import PremiumBusinesses from '../components/PremiumBusinesses';
import JourneySection from '../components/JourneySection';
import OwnerAnalyticsSection from '../components/OwnerAnalyticsSection';
import axios from 'axios';
import WaveBackground from '../components/WaveBackground';

export default function Home() {
  const [businesses, setBusinesses] = useState([]);
  const [filteredBusinesses, setFilteredBusinesses] = useState([]);
  const [vibeDataMap, setVibeDataMap] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [sortBy, setSortBy] = useState('vibe-score-high');

  // Fetch all businesses with vibe data
  useEffect(() => {
    const fetchBusinesses = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('/api/homepage');
        
        // Handle response structure - could be array directly or wrapped in businesses property
        const businesses = Array.isArray(response.data) 
          ? response.data 
          : (Array.isArray(response.data.businesses) ? response.data.businesses : []);
        
        console.log('Fetched businesses:', businesses);
        setBusinesses(businesses);

        // Build vibe data map from the response
        const vibeMap = {};
        businesses.forEach((business) => {
          if (business.latest_vibe) {
            const vibe = business.latest_vibe;
            const total = vibe.positive_count + vibe.negative_count;
            vibeMap[business.id] = {
              overall_score: vibe.vibe_score,
              sentiment_distribution: {
                positive: total > 0 ? vibe.positive_count / total : 0.5,
                negative: total > 0 ? vibe.negative_count / total : 0.5,
              },
              summary: vibe.summary_text || 'Guest experiences analyzed',
            };
          } else {
            // Default vibe data if no snapshot exists
            vibeMap[business.id] = {
              overall_score: 0.5,
              sentiment_distribution: {
                positive: 0.5,
                negative: 0.5,
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

    fetchBusinesses();
  }, []);


  // Filter and sort businesses based on search, location, and sort criteria
  useEffect(() => {
    let filtered = businesses.filter((business) => {
      const matchesSearch = business.name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const matchesLocation =
        !locationFilter ||
        (business.location &&
          business.location.toLowerCase().includes(locationFilter.toLowerCase()));
      return matchesSearch && matchesLocation;
    });

    // Sort businesses
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

    setFilteredBusinesses(filtered);
  }, [searchTerm, locationFilter, sortBy, businesses, vibeDataMap]);


  // Show loader while data is loading
  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004687] mx-auto mb-4" />
          <p className="text-gray-600">Discovering amazing resorts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white min-h-screen">
      {/* Hero Section with Search */}

        <WaveBackground
          height="300px"        // Height of the wave section (default: "300px")
          position="bottom"     // "top" or "bottom" (default: "bottom")
          opacity={0.08}        // Global opacity multiplier 0-1 (default: 0.08)
          animate={true}       // Enable floating animation (default: false)
          className=""          // Additional Tailwind classes
        />
      <div id="home">
        <HeroSection>
          <SearchBar onSearch={setSearchTerm} onLocationFilter={setLocationFilter} />
        </HeroSection>
      </div>

      {/* Premium Destinations (top 3) */}
      <section id="premium-businesses" className="scroll-mt-24">
        <PremiumBusinesses businesses={filteredBusinesses} vibeDataMap={vibeDataMap} />
      </section>

      {/* Journey section */}
      <section id="journey" className="scroll-mt-24">
        <JourneySection />
      </section>

    
      {/* Owner Analytics Section */}
      <OwnerAnalyticsSection />


      {/* Footer */}
      <Footer />
    </div>
  );
}
