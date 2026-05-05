import random

features = [
    "beachfront resort",
    "mountain resort",
    "island resort",
    "luxury villa",
    "family resort"
]

positive_aspects = [
    "clean rooms",
    "friendly staff",
    "amazing view",
    "relaxing atmosphere",
    "excellent service",
    "delicious food",
    "well-maintained facilities"
]

negative_aspects = [
    "dirty rooms",
    "slow service",
    "poor maintenance",
    "bad food quality",
    "noisy environment",
    "broken amenities",
    "unresponsive staff"
]

templates = [
    "Stayed at a {feature}. The place had {pos} and {pos2}. Overall very satisfying experience.",
    "Visited a {feature}. While the {pos} was great, the {neg} really affected our stay.",
    "The {feature} was decent. It had {pos} but also {neg}.",
    "At this {feature}, we experienced {neg} and disappointing service despite the nice location.",
    "Amazing stay at a {feature} with {pos} and incredible hospitality."
]


def generate_dynamic_review():
    feature = random.choice(features)
    pos1, pos2 = random.sample(positive_aspects, 2)
    neg = random.choice(negative_aspects)

    template = random.choice(templates)

    return template.format(
        feature=feature,
        pos=pos1,
        pos2=pos2,
        neg=neg
    )


def generate_reviews(n=100):
    return [generate_dynamic_review() for _ in range(n)]


if __name__ == "__main__":
    for r in generate_reviews(10):
        print(r)