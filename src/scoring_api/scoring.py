import random
from .store import store_cached

@store_cached
def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    score = 0
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    return score

def get_interests(store, cid):
    interests = store.get(f'interests:{cid}')
    if interests is None:
        interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
        store.set(f'interests:{cid}', interests)
    return random.sample(interests, 2)