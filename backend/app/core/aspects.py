# Core aspects and their associated keywords for Cosine Similarity-based ABSA in VibeCheck.
# This module defines the key aspects we analyze in customer reviews and the relevant keywords for each aspect
# that we use to identify sentences related to those aspects. This is crucial for our aspect-based sentiment analysis (ABSA) approach,
# where we want to determine sentiment not just at the review level but also at the aspect level

# can be expanded in the future to include more aspects or more sophisticated keyword sets, 
# but this provides a solid starting point for our ABSA implementation.
ASPECTS = {
    "food": (
        "food taste flavor menu meals dishes drinks beverages "
        "breakfast lunch dinner dessert cuisine ingredients "
        "portion serving fresh stale overcooked undercooked bland delicious"
        "food chicken meat taste texture flavor dry bland juicy rubbery chewy stale"
        "tastes like feels like texture like reminds me of"
    ),
    "service": (
        "service speed efficiency waiting queue slow fast prompt "
        "response delivery attentive neglect assistance helpdesk "
        "checkout reservation booking order processing"
    ),
    "staff": (
        "staff employees workers crew receptionist waiter waitress "
        "cashier guard management owner host hostess barista chef "
        "attitude behavior rude polite friendly unfriendly welcoming "
        "helpful unhelpful professional unprofessional courteous"
    ),
    "cleanliness": (
        "cleanliness hygiene sanitation dirty clean spotless filthy "
        "smell odor stain dusty maintained well-maintained bathroom "
        "toilet restroom linens towels pest insects rats"
    ),
    "price": (
        "price cost value expensive cheap affordable reasonable "
        "overpriced budget worth fee charge billing payment "
        "discount promo deal hidden charges"
    ),
    "ambience": (
        "ambience atmosphere vibe mood environment scenery view landscape beachfront oceanfront "
        "pool area garden tropical nature aesthetic design decor lighting sunset sunrise "
        "relaxing peaceful quiet luxury romantic cozy serene windy breezy"
    ),
    "location": (
        "location accessibility distance directions area island resort island resort access "
        "beachfront shoreline transport shuttle transfer airport distance travel time "
        "remote secluded private island central convenient hard to reach"
    ),
    "experience": (
        "experience stay visit vacation holiday resort stay overall satisfaction memorable "
        "enjoyable relaxing disappointing worth it recommend return service quality "
        "hospitality guest experience comfort luxury feel overall impression"
    ),
}


ASPECT_KEYWORDS = {
    aspect: set(keywords.split())
    for aspect, keywords in ASPECTS.items()
}