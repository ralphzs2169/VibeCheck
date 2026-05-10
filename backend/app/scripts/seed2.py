# Seed the database with sample data for testing and development.
# Usage: python -m backend.app.scripts.seed2

import asyncio
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from transformers import pipeline

from backend.app.core.aspects import ASPECTS
from backend.app.core.database import Base, engine
from backend.app.core.ml_registry import MLRegistry
from backend.app.core.security import hash_password
from backend.app.services.absa_service import run_absa_for_review
from backend.app.services.sentiment_service import analyze_sentiment_batch
from backend.app.services.vibe_snapshot_service import create_vibe_snapshot

from ..core.database import AsyncSessionLocal
from ..models.business import Business
from ..models.review import Review
from ..models.user import User

fake = Faker()

FIXED_PASSWORD = "09232929"

# -----------------------------
# Each resort has a raw pool of mixed reviews.
# The ML models will analyze and determine sentiment.
# Early reviews are written more negatively/neutrally,
# later reviews more positively (or vice versa) to simulate
# realistic vibe trajectories over time.
# -----------------------------

CEBU_RESORTS = [
    {
        "name": "Dalaguete Cove Resort",
        "location": "Dalaguete, Cebu",
        "description": "A peaceful cove resort nestled along the southern coast of Cebu, known for its clear waters and lush surroundings.",
        "vibe": "improving",
        # early reviews (indices 0-15): mostly complaints
        # mid reviews (indices 16-27): mixed
        # late reviews (indices 28-39): mostly praise
        "reviews": [
            "The rooms were dirty and the staff seemed uninterested in helping us.",
            "Very disappointing visit. The cove area had trash and maintenance was clearly lacking.",
            "Expected more based on the photos. Facilities are run down and the bathroom had mold.",
            "Staff were rude at check-in and our room had a broken air conditioner the whole stay.",
            "Not clean at all. Found insects in the room and nobody came to fix it despite complaints.",
            "Overpriced for the quality offered. Much better options available nearby.",
            "The beach area was not cleaned properly. Garbage near the waterline every morning.",
            "Terrible experience. Will not be returning. Management does not care about guests.",
            "The food was terrible and overpriced. The cove area had floating debris during our visit.",
            "Noisy generators at night made it impossible to sleep. Management was unapologetic.",
            "Dirty bathrooms, broken amenities, and indifferent staff. Avoid this place.",
            "The resort looks nothing like the photos. Very misleading advertising.",
            "Would not recommend to anyone. So many issues and zero accountability from management.",
            "The cove is pretty but the resort itself is a complete mess. So disappointed.",
            "Basic things like hot water and clean towels were not provided. Unacceptable.",
            "Staff were unhelpful and the food was bland and overpriced for the quality.",
            "The cove is beautiful but service is still inconsistent. Some staff are helpful, others are not.",
            "Decent stay overall but WiFi is weak and the restaurant menu is very limited.",
            "The location is great but some facilities need renovation. The cove swimming was lovely.",
            "Mixed experience. Staff friendliness varies a lot depending on who you encounter.",
            "Average for the price. The view is stunning but food quality needs serious improvement.",
            "The resort has potential but some areas need more attention and upkeep.",
            "Reasonable place to stay in Dalaguete. Acceptable but could be so much better.",
            "The cove view is stunning but the rooms felt a bit neglected. Service was average.",
            "Not bad but not great. The location is the main selling point of this resort.",
            "Comfortable enough stay. Some improvements are noticeable but more work is needed.",
            "Getting better but still has a way to go. The cove snorkeling is wonderful.",
            "Noticed improvements from our last visit. Staff seem more motivated now.",
            "The cove is stunning and the staff are now so much more attentive and helpful.",
            "Our recent visit was fantastic. The water is crystal clear and management has improved a lot.",
            "Loved our stay here. The hillside view of the cove at sunset is absolutely breathtaking.",
            "The resort has improved so much. Rooms are now spotless and breakfast is generous.",
            "Great hidden gem in the south of Cebu. Friendly staff and very peaceful surroundings.",
            "Finally a resort that lives up to its photos. The cove is gorgeous and staff are wonderful.",
            "We were pleasantly surprised. Much better than our visit a year ago. Highly recommend.",
            "The snorkeling in the cove is amazing. Staff provided equipment and guided us perfectly.",
            "Beautiful location and the service has improved drastically. Will definitely come back.",
            "One of the best stays in southern Cebu. Clean rooms, great food, stunning views.",
            "Cannot believe how much this resort has turned around. A real gem now.",
            "Perfect end to our Cebu trip. The cove, the staff, and the food were all excellent.",
        ],
    },
    {
        "name": "Simala Spring Resort",
        "location": "Sibonga, Cebu",
        "description": "A refreshing spring resort in the hills of Sibonga, offering natural pools and a tranquil retreat from city life.",
        "vibe": "kind_stable",
        # Consistently mixed to slightly positive — natural spring is the appeal
        "reviews": [
            "The natural spring pools are decent but the rooms are quite basic for the price.",
            "Nice concept with the spring pools but the resort facilities need more investment.",
            "The pools are refreshing but the resort gets very crowded on weekends.",
            "Average stay. The spring water is the main attraction. Everything else is just okay.",
            "Comfortable enough but WiFi was nonexistent and food options were very limited.",
            "The pools are great but the rooms felt damp and musty. Expected more.",
            "A reasonable retreat but nothing spectacular beyond the natural spring pools.",
            "Mixed feelings. The spring pools were wonderful but service was inconsistent.",
            "Decent value if you go mainly for the pools. The resort itself needs upkeep.",
            "The location is peaceful but resort amenities are quite basic compared to others.",
            "The natural spring pools at Simala are incredibly refreshing. A perfect city escape.",
            "Loved the cool spring water and lush greenery surrounding the resort. Very relaxing.",
            "Great resort for a quick getaway. The spring pools are clean and staff are friendly.",
            "The hillside setting is beautiful. Spring water was cold and the rooms were comfortable.",
            "Perfect weekend retreat. The natural pools were the highlight and food was good.",
            "Nice place to unwind. The spring pools are well-maintained and the staff are polite.",
            "A relaxing stay for the family. The kids loved the natural pools and the greenery.",
            "The pools were in good condition and the surrounding nature was lovely.",
            "Simala Spring is a decent resort. Pools are refreshing and staff are helpful.",
            "Good experience overall. The spring pools are unique and the setting is peaceful.",
            "The natural pools are the reason to visit and they did not disappoint at all.",
            "A lovely retreat from city life. The spring water was cool and the air was fresh.",
            "Reasonable stay. The spring pools are well worth the trip to Sibonga.",
            "The resort has a calm atmosphere and the natural spring is genuinely refreshing.",
            "Nice weekend spot. The pools were clean and the staff kept things well managed.",
            "Enjoyed our stay at Simala Spring. The natural pools were the highlight for sure.",
            "The spring resort concept is great. Execution is decent and the pools are lovely.",
            "Good value for what it offers. The natural spring experience is unique in Cebu.",
            "A pleasant stay. The spring pools were relaxing and the hillside views were nice.",
            "Would recommend for a short nature getaway. The pools are the star attraction.",
            "The pools were refreshing after a hot drive. Staff were welcoming and helpful.",
            "Nice hidden retreat in Sibonga. The spring water is genuinely cool and revitalizing.",
            "The resort is modest but the spring pools are excellent. A worthwhile visit.",
            "Enjoyed the peaceful hillside setting. The spring pools made our stay memorable.",
            "A calm and refreshing stay. The natural spring is a unique experience in Cebu.",
            "Good resort for nature lovers. The spring pools are clean and well maintained.",
            "The spring water was so refreshing. Staff were friendly and the setting was lovely.",
            "A relaxing stay surrounded by nature. The pools were the highlight of our trip.",
            "Simala Spring delivers on its promise of a natural retreat. The pools are great.",
            "Would visit again. The spring pools are unlike anything else in southern Cebu.",
        ],
    },
    {
        "name": "Malapascua Tide Resort",
        "location": "Malapascua Island, Cebu",
        "description": "A charming island resort in Malapascua, popular among divers and beach lovers seeking an off-the-beaten-path experience.",
        "vibe": "stable",
        # Consistently positive — world class diving destination
        "reviews": [
            "Malapascua Tide is the perfect base for diving. The thresher shark dives were unforgettable.",
            "Absolutely loved this resort. The island vibe is amazing and staff are so warm.",
            "Best diving resort we have stayed at in the Philippines. Excellent dive operators.",
            "The white sand beach right in front of the resort is stunning. Snorkeling was incredible.",
            "Perfect island escape. The resort is charming and the surrounding waters are world-class.",
            "We came for the diving and stayed for the overall resort experience. Fantastic.",
            "The staff here are exceptional. They arranged all our dives and made us feel like family.",
            "Magical island resort. Woke up every morning to the sound of waves and amazing sunrises.",
            "The food at the resort restaurant uses fresh local seafood. Every meal was delicious.",
            "Highly recommend Malapascua Tide to any diver or beach lover. Truly a special place.",
            "The thresher shark dive at dawn was the most incredible experience of my life.",
            "The resort has such a genuine island feel. Nothing pretentious, just pure relaxation.",
            "Loved waking up to the sound of the ocean every single morning. Pure paradise.",
            "The dive instructors here are among the best we have encountered anywhere in Asia.",
            "Fresh catch from local fishermen served at the resort restaurant every day. Amazing.",
            "The beach here is absolutely pristine. Crystal clear water and soft white sand.",
            "A truly special place. The marine biodiversity around Malapascua is breathtaking.",
            "The resort arranged a night dive that was unlike anything we had experienced before.",
            "Warm hospitality and world-class diving. Malapascua Tide delivers on every level.",
            "The island has a magical atmosphere and the resort captures it perfectly.",
            "One of the top diving destinations in the world and this resort does it justice.",
            "Every staff member here genuinely loves what they do. It shows in the experience.",
            "The coral gardens around the island are incredibly healthy and vibrant.",
            "We extended our stay by three days because we simply could not leave. That says it all.",
            "The resort is simple but everything that matters is done exceptionally well.",
            "Incredible diving, beautiful beach, fresh seafood, and wonderful people. Perfect.",
            "Malapascua Island itself is a gem and this resort is the best way to experience it.",
            "The sunset from the resort beach every evening was absolutely stunning.",
            "We have traveled across Southeast Asia and this is one of our all-time favorite stays.",
            "The dive shop here is professionally run and the equipment is always in great condition.",
            "A hidden paradise. The resort is intimate and the service feels personal and genuine.",
            "The local fishing village nearby adds so much authentic charm to the experience.",
            "Loved every single moment of our stay. Would come back every year if we could.",
            "The thresher sharks at Monad Shoal were worth the early 4am wake-up call.",
            "A resort that truly respects the marine environment. Responsible and wonderful.",
            "The rooms are simple but very clean and comfortable. The location makes everything perfect.",
            "Best island vacation we have ever had. The diving, food, and people were all outstanding.",
            "The resort staff remembered our names and preferences from day one. Exceptional service.",
            "A world-class dive destination with a resort that matches the quality of the experience.",
            "We came as strangers and left feeling like part of the Malapascua community.",
        ],
    },
    {
        "name": "Bantayan Breeze Resort",
        "location": "Bantayan Island, Cebu",
        "description": "A breezy beachfront resort on Bantayan Island with powdery white sand and stunning sunset views.",
        "vibe": "declining",
        # Early reviews are glowing, later ones show a resort in decline
        "reviews": [
            "Bantayan Breeze was absolutely wonderful. The white sand beach is one of the best in Cebu.",
            "The sunset views from the resort dining area were the most beautiful we have ever seen.",
            "Had a wonderful stay. The sea breeze from our room was so refreshing and food was great.",
            "Beautiful beachfront resort. The staff were lovely and the facilities were spotless.",
            "Loved every moment here. The beach is pristine and staff made us feel so welcome.",
            "One of the top resorts on Bantayan Island. Cannot recommend it enough.",
            "The beachfront breakfast was magical. Fresh food and stunning ocean views every morning.",
            "The resort has such a lovely atmosphere. Clean, breezy, and wonderfully relaxing.",
            "Staff were incredibly attentive and the rooms were immaculate. Will definitely return.",
            "A paradise resort on a paradise island. Bantayan Breeze exceeded all our expectations.",
            "Still a beautiful location but the service has noticeably slipped since our last visit.",
            "The beach is gorgeous but the resort seems to be coasting on its reputation now.",
            "Beautiful beach but the rooms need renovation. Noticed wear and tear throughout.",
            "The food quality has gone down since our last visit. The beach is still the highlight.",
            "Mixed experience. The sunset views are incredible but the service was disappointing.",
            "The resort is showing its age. Some areas maintained but others are clearly neglected.",
            "Good location but staff turnover seems high. Service was inconsistent throughout stay.",
            "The beach is gorgeous but the resort facilities need serious attention and investment.",
            "Not as good as before. The resort needs investment to match the beauty of its location.",
            "Average stay. Expected more given the price. The beach saved the experience.",
            "Very disappointing visit. The resort has clearly declined. Rooms were dirty.",
            "Cannot believe how much this resort has gone downhill. Not worth the price anymore.",
            "The beach is still beautiful but the resort itself is a complete mess now.",
            "Staff were rude and unhelpful. The food was terrible and overpriced for the quality.",
            "Found mold in the bathroom and the air conditioning was broken. Management did not care.",
            "Would not return. The resort has deteriorated significantly since our last visit.",
            "Terrible service and dirty facilities. The only good thing was the beach itself.",
            "Overpriced and underdelivering. Living off its old reputation at this point.",
            "Had high expectations based on old reviews but was completely let down. Very sad.",
            "The worst resort experience we have had in Cebu. So many unresolved issues.",
            "Unacceptable conditions for the price. The beach is free but the resort costs too much.",
            "Staff seem demotivated and management appears absent. The decline is very visible.",
            "Rooms were not cleaned before check-in. Found the previous guest belongings still there.",
            "The pool had visible algae and nobody seemed concerned about maintaining it.",
            "Spent two nights here and both were uncomfortable due to broken AC and noisy pipes.",
            "The restaurant has reduced its menu drastically and quality has fallen off a cliff.",
            "A resort that was once great is now a shadow of its former self. Very disappointing.",
            "The beachfront is still lovely but everything behind it has been neglected badly.",
            "We left a day early because the conditions were simply not acceptable for the price.",
            "Avoid until management makes serious changes. The decline is steep and fast.",
        ],
    },
    {
        "name": "Moalboal Reef Resort",
        "location": "Moalboal, Cebu",
        "description": "A diver's paradise resort in Moalboal, steps away from the famous sardine run and vibrant coral reefs.",
        "vibe": "stable",
        # Consistently excellent — world famous dive site
        "reviews": [
            "The sardine run right off the shore is one of the most incredible things I have ever seen.",
            "Perfect resort for diving. The reef is steps away and the dive shop is excellent.",
            "Moalboal Reef Resort exceeded all our expectations. Clean rooms and world-class diving.",
            "The coral walls here are stunning. The resort arranged all our dives perfectly.",
            "Came for the sardines and stayed for the overall experience. Fantastic resort.",
            "The dive instructors here are among the best we have encountered in the Philippines.",
            "Woke up every morning excited to dive. Resort facilities are great and staff are top-notch.",
            "Amazing snorkeling and diving right from the shore. Comfortable and well-run resort.",
            "The best dive resort experience in Cebu. Highly organized and underwater world is magical.",
            "Fresh seafood at the resort restaurant after a day of diving. Could not ask for more.",
            "The sardine tornado was unlike anything I have ever witnessed. Absolutely breathtaking.",
            "The resort keeps the reef clean and takes marine conservation seriously. Admirable.",
            "Every dive here reveals something new and incredible. The biodiversity is stunning.",
            "The shore entry for diving is easy and the reef drops off immediately. Just incredible.",
            "The dive shop is professionally managed and all equipment is in excellent condition.",
            "We came for a weekend and extended to a full week. The diving is that good.",
            "The turtles we encountered during our morning dive were so relaxed around divers.",
            "The resort restaurant sources everything locally and the seafood is incredibly fresh.",
            "A genuinely world-class dive destination with a resort that matches the experience.",
            "The staff are passionate about diving and the marine environment. It shows in everything.",
            "We have dived across Asia and Moalboal remains one of our absolute favorites.",
            "The coral is incredibly healthy and the variety of marine life is extraordinary.",
            "The resort provides excellent dive briefings and the guides know every inch of the reef.",
            "Loved the atmosphere here. Fellow guests were all dive enthusiasts and the vibe was great.",
            "The sunset at Moalboal is gorgeous. A perfect end to a day of incredible diving.",
            "The resort is modest but everything that matters for a dive trip is done perfectly.",
            "Night dives arranged by the resort were spectacular. Saw things we had never seen before.",
            "The sardine run was so thick it blocked out the sunlight. An unforgettable experience.",
            "Friendly and knowledgeable dive guides who genuinely care about your experience.",
            "One of the few places in the world where the reef is this close to the shore.",
            "The resort staff went out of their way to ensure we had the perfect dive trip.",
            "Cannot recommend Moalboal Reef Resort highly enough to any diver visiting Cebu.",
            "The marine life diversity here is extraordinary. Every dive was different and exciting.",
            "Fresh tuna for dinner after diving with tuna in the morning. Life does not get better.",
            "The resort takes care of all logistics so you can focus entirely on diving.",
            "We left with hundreds of underwater photos and memories that will last a lifetime.",
            "The reef here should be on every diver's bucket list. And this resort is the best base.",
            "Exceptional service, clean facilities, and diving that is simply second to none.",
            "The dive shop owner is incredibly knowledgeable about the local marine ecosystem.",
            "Everything about this resort is geared towards giving divers the best possible experience.",
        ],
    },
    {
        "name": "Mactan Shoreline Resort",
        "location": "Mactan Island, Cebu",
        "description": "A convenient beachfront resort on Mactan Island, ideal for families and travelers looking for comfort near the city.",
        "vibe": "improving",
        # Starts rocky, improves noticeably over time
        "reviews": [
            "Noisy resort due to proximity to the airport. Could hear planes throughout the night.",
            "The beach water quality was poor during our visit. Not suitable for swimming at all.",
            "Overpriced for what is essentially an airport hotel with a small beach attached.",
            "Staff were undertrained and unhelpful. Basic requests took forever to be fulfilled.",
            "Dirty rooms and poor maintenance. Expected much better for the price they charge.",
            "The pool area was not cleaned properly. Found debris floating in it on arrival.",
            "Staff seemed confused about our reservation. Check-in took over an hour.",
            "The food at the restaurant was mediocre and very overpriced for the quality served.",
            "Broken bathroom fixtures and no hot water during our entire stay. Unacceptable.",
            "The resort photos are very misleading. The actual beach is tiny and not well-kept.",
            "Some improvements visible but still inconsistent. The beach area is getting better.",
            "Decent location near the airport but the resort itself is still average overall.",
            "Noticed some renovation work. Rooms are cleaner now but could still use more work.",
            "Mixed stay. Some staff were great while others seemed undertrained still.",
            "Acceptable for a short stopover near the airport. Not a destination resort yet.",
            "The beach area has improved. Pool is cleaner now and the food has gotten better.",
            "Getting better with each visit. Staff are more professional and rooms are cleaner.",
            "The family rooms are spacious and the renovation is making a real difference.",
            "Much better than our visit last year. The management has clearly been working hard.",
            "Improvements are visible everywhere. The beachfront area is now well-maintained.",
            "Mactan Shoreline has really stepped up. The beachfront area is beautifully maintained.",
            "So impressed with how much this resort has improved. Staff are professional now.",
            "Perfect location near the airport. The resort has improved significantly.",
            "The family rooms are spacious and well-equipped. Kids loved the pool and beach.",
            "Great convenience of being close to Cebu City while still having a beach experience.",
            "The renovation has done wonders. Rooms are fresh and modern and service is much better.",
            "Lovely resort for a family vacation. Staff were incredibly helpful with our children.",
            "The beachfront sunset views are gorgeous. The new restaurant menu is excellent.",
            "Much better than our visit two years ago. Management has invested in real improvements.",
            "Comfortable and well-located. The beach is well-maintained and staff are attentive.",
            "The kids had the best time here. The pool is clean and the beach is safe and calm.",
            "A wonderful family resort that has really turned things around. Highly recommend.",
            "The staff go out of their way to make families feel welcome. Truly impressive now.",
            "Clean rooms, great food, and a beautiful beachfront. What a transformation.",
            "We were skeptical based on old reviews but this resort has really improved.",
            "The new restaurant menu is excellent and the beachfront sunset is breathtaking.",
            "Everything feels fresh and well-managed now. A completely different resort experience.",
            "Genuinely impressed by the improvements here. Staff are warm and professional.",
            "One of the best family resort experiences we have had in Cebu. Highly recommend.",
            "The transformation of this resort is remarkable. Will definitely come back.",
        ],
    },
    {
        "name": "Camotes Sea Lodge",
        "location": "Camotes Island, Cebu",
        "description": "A laid-back lodge on Camotes Island surrounded by rolling hills, lagoons, and quiet beaches perfect for unwinding.",
        "vibe": "kind_stable",
        # Consistently okay to decent — simple island lodge
        "reviews": [
            "Camotes Sea Lodge is a nice quiet retreat but facilities are very basic.",
            "The island is lovely but the lodge itself needs more investment in amenities.",
            "Peaceful location but WiFi is nonexistent and the food options are very limited.",
            "Good for a simple getaway but do not expect any luxury at all here.",
            "The boat ride to get here can be long and rough in bad weather. Plan accordingly.",
            "Decent accommodation for the price on Camotes. Beach is quiet and unspoiled.",
            "Acceptable for nature lovers but too basic for those expecting resort-level comfort.",
            "The lagoon visit was the highlight. The lodge itself is simple but clean enough.",
            "Good enough for a few nights on Camotes. Limited activities but scenery is beautiful.",
            "A relaxing stay in a quiet setting. Do not expect much and you will not be disappointed.",
            "Camotes Sea Lodge is the perfect off-grid escape. The lagoon nearby is magical.",
            "Loved the laid-back atmosphere of this lodge. Camotes Island is underrated and beautiful.",
            "The rolling hills and quiet beach made this one of our most peaceful vacations.",
            "Charming lodge with a great local feel. Staff are warm and food is home-cooked style.",
            "Perfect for unplugging from the city. No crowds, no noise, just nature and relaxation.",
            "The lagoon nearby is absolutely stunning. Worth the trip to Camotes just for that.",
            "Simple and genuine. The local hospitality here is the kind you cannot manufacture.",
            "A peaceful island escape that recharges you completely. The lodge is modest but clean.",
            "Camotes is such an underrated island and this lodge captures its charm perfectly.",
            "The staff here are genuinely warm and make you feel like a welcome guest.",
            "Nice quiet beach and friendly staff. The lodge is basic but everything you need is there.",
            "A good base for exploring Camotes Island. The lodge is comfortable enough.",
            "The surrounding nature is beautiful. The lodge itself is simple but well kept.",
            "We loved the simplicity of this lodge. No pretension, just genuine island hospitality.",
            "A relaxing stay away from the tourist crowds. The island is beautiful and peaceful.",
            "The lodge does what it promises. A simple, relaxing stay on a beautiful island.",
            "Camotes Sea Lodge has a real charm to it. Simple, honest, and genuinely restful.",
            "The sunsets from the lodge beach area were quiet and beautiful. Very peaceful.",
            "We left feeling genuinely rested. The island pace here is exactly what we needed.",
            "A decent lodge for exploring Camotes. Staff are helpful and the location is lovely.",
            "The natural surroundings make up for the basic facilities. A good nature retreat.",
            "Simple accommodation but the island more than compensates. Camotes is beautiful.",
            "Friendly staff and a relaxed atmosphere. A good choice for a quiet island escape.",
            "The lodge is unpretentious and the island is stunning. A winning combination.",
            "Enjoyed the peace and quiet here. The lodge is basic but that fits the island vibe.",
            "A genuine island experience. No frills but lots of natural beauty and warm people.",
            "The lagoon, the rolling hills, and the quiet beach make Camotes worth visiting.",
            "We spent three nights here completely offline and felt completely refreshed.",
            "A simple lodge in a beautiful setting. Exactly what a Camotes escape should be.",
            "Would recommend to anyone looking for a genuine off-the-beaten-path island stay.",
        ],
    },
    {
        "name": "Oslob Whale Haven Resort",
        "location": "Oslob, Cebu",
        "description": "A scenic resort near the famous whale shark sanctuary in Oslob, offering guided encounters and seaside relaxation.",
        "vibe": "declining",
        # Starts strong on the whale shark experience, declines into neglect
        "reviews": [
            "The whale shark encounter organized by the resort was incredible and responsibly run.",
            "Loved our stay here. The whale shark experience was a once in a lifetime moment.",
            "The resort staff arranged a wonderful whale shark tour. Rooms were comfortable.",
            "Beautiful seaside resort with easy access to the whale shark sanctuary. Loved it.",
            "The highlight of our Cebu trip. The resort and whale shark experience were fantastic.",
            "The whale shark encounter was breathtaking. Staff were knowledgeable and responsible.",
            "Waking up early for the whale sharks was absolutely worth it. A magical experience.",
            "The resort location right near the sanctuary makes it the best place to stay in Oslob.",
            "Staff were warm and welcoming. The whale shark tour was organized professionally.",
            "An unforgettable stay. The whale sharks were magnificent and the resort was lovely.",
            "Good location for the whale shark tour but the resort itself is starting to slip.",
            "The whale shark encounter was amazing but the resort facilities need improvement.",
            "Decent stay. The whale shark experience is the reason to come, not the resort.",
            "The resort is showing signs of neglect. The whale shark tour made up for it.",
            "Mixed experience. The tour was great but the food at the resort was disappointing.",
            "The location near the sanctuary is convenient but the resort is overpriced now.",
            "Acceptable accommodation for the whale shark experience but not much more.",
            "The whale sharks were breathtaking. The resort itself was just average at best.",
            "Good enough for one night before the whale shark tour. Nothing more, nothing less.",
            "The sanctuary experience was wonderful but the resort has clearly seen better days.",
            "The resort has really declined. Dirty rooms, poor food, and staff who do not care.",
            "Would not stay here again. The rooms were musty and the service was terrible.",
            "Only came for the whale sharks but the resort experience was a complete letdown.",
            "Overpriced and underdelivering. Coasting entirely on the whale shark attraction.",
            "Staff were rude and the facilities were in poor condition. Very disappointing.",
            "The whale shark tour was managed poorly and the resort itself was dirty.",
            "Cannot believe how bad this resort has gotten. Find better options in Oslob.",
            "Terrible value for money. The resort relies entirely on whale sharks to attract guests.",
            "Found the rooms unacceptable. Stains on sheets and the bathroom was not cleaned.",
            "The worst resort experience of our Cebu trip. Management needs to step up.",
            "Rooms smelled of mildew and the restaurant served cold food. Avoid.",
            "The decline here is shocking. This resort used to have a great reputation.",
            "Staff showed zero interest in guest concerns. Complained three times and nothing changed.",
            "The whale sharks saved this trip but the resort nearly ruined it. Very frustrating.",
            "Overpriced by a significant margin for what is now a poorly maintained resort.",
            "Would not recommend to anyone. Better to stay elsewhere and just day trip for the sharks.",
            "The facilities are in a sorry state. Broken furniture, dirty bathrooms, absent staff.",
            "Management appears to have completely given up on maintaining any standards here.",
            "A resort that had so much potential now running entirely on the whale shark hype.",
            "Our worst accommodation experience in Cebu by a significant margin. Avoid.",
        ],
    },
    {
        "name": "Alegria Cliff Resort",
        "location": "Alegria, Cebu",
        "description": "A cliffside resort in southern Cebu overlooking the Tañon Strait, offering breathtaking views and adventure activities.",
        "vibe": "stable",
        # Consistently excellent — stunning unique location
        "reviews": [
            "The clifftop views over the Tañon Strait are absolutely jaw-dropping. A stunning resort.",
            "Alegria Cliff Resort is one of the most unique stays in all of Cebu. The views are unreal.",
            "The zip line activity from the cliff was thrilling and the scenery was breathtaking.",
            "Woke up to the most incredible sunrise over the strait. The resort staff are wonderful.",
            "Perfect for adventure seekers. The cliff activities and the scenery make this truly special.",
            "The food here is surprisingly excellent. Fresh local ingredients with stunning views to match.",
            "One of the most memorable resort stays in our lives. The cliff setting is magical.",
            "The resort offers a perfect mix of adventure and relaxation. Highly recommend.",
            "Staff are incredibly passionate about the resort and it shows in every single detail.",
            "The Tañon Strait views at sunset are worth every peso. Fantastic resort overall.",
            "Watching the fishing boats sail past from the clifftop was such a peaceful experience.",
            "The cliff setting makes every moment here feel cinematic and special.",
            "We did the cliff jump activity and it was the most exhilarating thing we have ever done.",
            "The staff organized a bonfire on the cliff edge at night. Absolutely magical.",
            "Fresh local produce and catch from nearby fishermen. The food is genuinely excellent.",
            "The resort feels like a carefully kept secret. Not too crowded and beautifully managed.",
            "Waking up to a sea of clouds below the cliff was an experience we will never forget.",
            "The adventure activities are well-supervised and the guides are experienced and fun.",
            "The cliff resort concept is perfectly executed here. Views, activities, and hospitality.",
            "We stayed for two nights and wished we had booked for a week. Truly special.",
            "The views across the Tañon Strait at golden hour are absolutely breathtaking.",
            "A resort that genuinely feels unique and not replicated anywhere else in Cebu.",
            "The passion of the staff makes everything here feel personal and special.",
            "From the cliff top we watched dolphins playing in the strait below. Unforgettable.",
            "The food at the cliff restaurant is far better than you would expect. Excellent quality.",
            "We watched the most spectacular lightning storm from the cliff safety of the resort.",
            "Every detail of this resort has been thought through. A truly excellent experience.",
            "The cliff setting attracts the most amazing cloud formations and sunsets.",
            "A resort that offers genuine adventure alongside genuine comfort and hospitality.",
            "The staff here have real pride in their resort and it shows in everything they do.",
            "The zipline over the cliff into the forest was absolutely incredible and perfectly safe.",
            "We came for the views and stayed for the whole experience. Could not have been better.",
            "The most unique resort setting we have encountered in all of Southeast Asia.",
            "The cliff views make every meal, every morning, and every moment here feel special.",
            "Adventure activities, incredible food, and views that take your breath away.",
            "A resort that genuinely deserves all the praise it receives. A true hidden gem.",
            "The stars from the clifftop at night were the most spectacular we have ever seen.",
            "Perfect combination of adventure, nature, great food, and wonderful hospitality.",
            "The Tañon Strait from the clifftop is one of the most beautiful views in the Philippines.",
            "Alegria Cliff Resort is genuinely one of the best resorts we have stayed at anywhere.",
        ],
    },
    {
        "name": "Sogod Bay Resort",
        "location": "Sogod, Cebu",
        "description": "A hidden gem resort along Sogod Bay, known for its unspoiled beaches, fresh seafood, and friendly local hospitality.",
        "vibe": "improving",
        # Starts rough, steadily improves into a genuinely good resort
        "reviews": [
            "Too remote and the facilities are not ready for guests at all. Very disappointing.",
            "The resort advertises things that are simply not available yet. Very misleading.",
            "Rooms were not properly furnished and basic amenities were completely missing.",
            "The road to the resort is terrible and damaged our vehicle. Management was unapologetic.",
            "Expected a hidden gem but found a half-finished resort. Will not return until ready.",
            "The beach is beautiful but the resort cannot support guests properly yet.",
            "Found the kitchen understaffed and the menu had almost nothing available.",
            "No running hot water and the generator cut out twice during our stay.",
            "Staff were well-meaning but clearly untrained and unprepared for guests.",
            "The bay is stunning but the resort is simply not ready to host visitors yet.",
            "Starting to show some improvement but still has significant gaps in service.",
            "The bay is beautiful and the staff are getting more organized with each visit.",
            "Rough around the edges but you can see the potential. The seafood is excellent.",
            "Better than our last visit. Some facilities now working properly. Improving.",
            "Mixed stay. The bay is gorgeous and the staff are friendlier. Food has improved.",
            "The resort is developing well. Not perfect yet but heading in the right direction.",
            "The fresh seafood is now consistently excellent. The rooms have been cleaned up.",
            "Noticeable improvements across the board. The staff seem more confident now.",
            "Getting better with each visit. The bay is stunning and the hospitality is warming up.",
            "Almost there. A few more improvements and this will be a genuinely great resort.",
            "Sogod Bay Resort is a true hidden gem now. The bay is pristine and seafood incredible.",
            "So glad we discovered this resort. The beach is unspoiled and staff are so genuine.",
            "The freshest seafood we have had in all of Cebu. The resort has really improved.",
            "A wonderful hidden resort that more people should know about. Beautiful bay.",
            "The snorkeling in the bay is amazing. The resort has clearly invested in improvements.",
            "Lovely quiet resort away from the tourist crowds. The local hospitality is heartwarming.",
            "The resort has come a long way. Rooms are now comfortable and the food is fantastic.",
            "One of the best kept secrets in Cebu. The bay is stunning and the resort is charming.",
            "The staff here feel like family. Such genuine hospitality and the seafood is excellent.",
            "Wonderful experience from start to finish. The bay, the food, and the people are special.",
            "Cannot believe we almost missed this place. The bay is gorgeous and the resort is lovely.",
            "A hidden paradise that has grown into a genuinely wonderful resort experience.",
            "The transformation of this resort is remarkable. From rough start to real gem.",
            "The local fishermen supply the restaurant daily. The seafood could not be fresher.",
            "We snorkeled in the bay every morning. The marine life is abundant and beautiful.",
            "The staff pride in their resort is now so visible. It makes the whole experience warm.",
            "A resort that has worked hard to earn its place as a hidden gem. Well deserved.",
            "The bay at dawn with no other guests around is one of the most peaceful things ever.",
            "Sogod Bay is everything a hidden gem should be. Unspoiled, genuine, and beautiful.",
            "Will tell everyone we know about this resort. A true discovery in southern Cebu.",
        ],
    },
]


async def get_first_review_date(db, business_id: int):
    result = await db.execute(
        select(Review.created_at).where(
            Review.business_id == business_id
        ).order_by(Review.created_at.asc()).limit(1)
    )
    return result.scalar()


async def backfill_vibe_snapshots(db, business_id: int, models: MLRegistry):
    first_date = await get_first_review_date(db, business_id)

    if not first_date:
        return

    if first_date.tzinfo is None:
        first_date = first_date.replace(tzinfo=timezone.utc)
    else:
        first_date = first_date.astimezone(timezone.utc)

    today = datetime.now(timezone.utc)
    current = first_date
    snapshots_created = 0

    while current <= today:
        snapshot = await create_vibe_snapshot(
            db,
            business_id,
            models,
            snapshot_date=current,
            use_ai_summary=False,
        )
        if snapshot is not None:
            snapshots_created += 1
        current += timedelta(days=1)

    if snapshots_created > 0:
        print(f"  Created {snapshots_created} snapshots for {business_id}")


def get_review_for_business(resort: dict, index: int, total: int) -> str:
    """
    Pick a review from the resort's raw pool based on position in time.
    For improving resorts: early reviews are from the start of the list (worse),
    later reviews from the end (better). For declining: reversed.
    For stable/kind_stable: random from entire pool.
    Reviews are NOT pre-labeled — the ML model determines sentiment.
    """
    reviews = resort["reviews"]
    vibe = resort["vibe"]
    progress = index / total

    if vibe == "improving":
        # Early = pick from first half, late = pick from second half
        if progress < 0.4:
            pool = reviews[:len(reviews)//3]
        elif progress < 0.7:
            pool = reviews[len(reviews)//3: 2*len(reviews)//3]
        else:
            pool = reviews[2*len(reviews)//3:]
    elif vibe == "declining":
        # Early = pick from second half (good), late = pick from first half (bad)
        if progress < 0.4:
            pool = reviews[2*len(reviews)//3:]
        elif progress < 0.7:
            pool = reviews[len(reviews)//3: 2*len(reviews)//3]
        else:
            pool = reviews[:len(reviews)//3]
    else:
        # stable / kind_stable — random from full pool
        pool = reviews

    return random.choice(pool)


def generate_created_at_with_bias() -> datetime:
    start, end = random.choices([
        ("-6M", "-5M"),
        ("-5M", "-4M"),
        ("-4M", "-3M"),
        ("-3M", "-2M"),
        ("-2M", "-1M"),
        ("-1M", "now"),
    ], weights=[1]*6)[0]

    dt = fake.date_time_between(start_date=start, end_date=end)
    return dt.replace(tzinfo=timezone.utc)


async def seed() -> None:
    print("Loading ML models...")

    sentiment_model = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )

    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    aspect_texts = list(ASPECTS.values())
    aspect_embeddings = embedding_model.encode(aspect_texts, convert_to_tensor=True)
    keyword_extractor_model = KeyBERT(model=embedding_model)

    models = MLRegistry(
        sentiment=sentiment_model,
        embedding=embedding_model,
        aspect_embeddings=aspect_embeddings,
        keyword_extractor=keyword_extractor_model
    )

    async with AsyncSessionLocal() as db:

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await db.execute(Review.__table__.delete())
        await db.execute(Business.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()

        # 10 owners + 10 reviewers
        print("Seeding users...")

        users = []
        owners = []

        for _ in range(10):
            owner = User(
                username=fake.unique.user_name(),
                firstname=fake.first_name(),
                lastname=fake.last_name(),
                role="owner",
                hashed_password=hash_password(FIXED_PASSWORD),
            )
            db.add(owner)
            owners.append(owner)
            users.append(owner)

        for _ in range(10):
            user = User(
                username=fake.unique.user_name(),
                firstname=fake.first_name(),
                lastname=fake.last_name(),
                role="reviewer",
                hashed_password=hash_password(FIXED_PASSWORD),
            )
            db.add(user)
            users.append(user)

        await db.commit()
        for u in users:
            await db.refresh(u)

        # 10 Cebu Resorts
        print("Seeding businesses...")

        businesses = []

        for i, resort in enumerate(CEBU_RESORTS):
            business = Business(
                name=resort["name"],
                location=resort["location"],
                short_description=resort["description"],
                image_path=None,
                owner_id=owners[i].id
            )
            db.add(business)
            businesses.append(business)

        await db.commit()
        for b in businesses:
            await db.refresh(b)

        # 40 reviews per business = 400 total
        print("Seeding reviews...")

        review_objects = []
        review_meta = []

        reviews_per_business = 40

        for i, business in enumerate(businesses):
            resort = CEBU_RESORTS[i]

            for j in range(reviews_per_business):
                created_at = generate_created_at_with_bias()
                review_text = get_review_for_business(resort, j, reviews_per_business)
                review_meta.append((review_text, business, created_at))

        review_texts = [r[0] for r in review_meta]
        results = analyze_sentiment_batch(review_texts, models.sentiment)

        for (text, business, created_at), (score, label, _) in zip(review_meta, results):
            review = Review(
                content=text,
                sentiment_label=label,
                sentiment_score=score,
                user_id=random.choice(users).id,
                business_id=business.id,
                created_at=created_at,
            )
            db.add(review)
            review_objects.append(review)

        await db.commit()
        for r in review_objects:
            await db.refresh(r)

        print("Running ABSA...")
        for review in review_objects:
            await run_absa_for_review(db, review, models)
        await db.commit()

        print("Creating vibe snapshots...")
        for business in businesses:
            print(f"  Backfilling {business.name}...")
            await backfill_vibe_snapshots(db, business.id, models)
        await db.commit()

        print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())