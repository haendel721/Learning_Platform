from rest_framework.throttling import UserRateThrottle


class AIGenerationThrottle(UserRateThrottle):
    # 'scope' doit correspondre exactement à la clé définie
    # dans DEFAULT_THROTTLE_RATES ci-dessus
    scope = 'ai_generation'