ASPECTS = {
    "food": (
        "food taste flavor menu meals dishes drinks beverages "
        "breakfast lunch dinner dessert cuisine ingredients "
        "portion serving fresh stale overcooked undercooked bland delicious"
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
        "ambience atmosphere vibe mood environment noise music "
        "lighting decor interior design cozy romantic crowded "
        "peaceful relaxing loud chaotic aesthetic themed view scenery"
    ),
    "location": (
        "location parking accessibility distance directions area "
        "neighborhood nearby transport commute entrance exit "
        "remote convenient central accessible hard to find"
    ),
    "experience": (
        "experience visit stay overall satisfaction memorable "
        "enjoyable disappointing recommend return worth "
        "impression feeling overall quality"
    ),
}

ASPECT_KEYWORDS = {
    aspect: set(keywords.split())
    for aspect, keywords in ASPECTS.items()
}