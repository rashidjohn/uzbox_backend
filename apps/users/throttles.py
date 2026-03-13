from rest_framework.throttling import AnonRateThrottle


class LoginThrottle(AnonRateThrottle):
    """Login endpointiga brute-force himoya: 5/daqiqa"""
    rate  = "5/minute"
    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    """Register spam himoya: 3/daqiqa"""
    rate  = "3/minute"
    scope = "register"


from rest_framework.throttling import ScopedRateThrottle

class CheckoutThrottle(ScopedRateThrottle):
    scope = "checkout"

class PromoCheckThrottle(ScopedRateThrottle):
    scope = "promo_check"

class ReviewThrottle(ScopedRateThrottle):
    scope = "review"

class VerifyEmailThrottle(ScopedRateThrottle):
    scope = "verify_email"

class PasswordThrottle(ScopedRateThrottle):
    scope = "password"

class WishlistThrottle(ScopedRateThrottle):
    scope = "wishlist"
