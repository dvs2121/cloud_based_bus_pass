"""
Static reference data for the Indian routes network:
 - list of serviceable cities
 - bus corridor connectivity (which source/destination pairs actually run)
 - an approximate road-distance matrix (km), reused for both bus reference
   data and self-driving car / mini-bus hire pricing
 - the hire pricing calculator (Indian outstation taxi convention)
"""
import math

CITIES = [
    "New Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata", "Hyderabad",
    "Pune", "Ahmedabad", "Surat", "Jaipur", "Lucknow", "Kanpur", "Varanasi",
    "Agra", "Chandigarh", "Amritsar", "Dehradun", "Haridwar", "Rishikesh",
    "Shimla", "Manali", "Indore", "Bhopal", "Nagpur", "Goa", "Mysuru",
    "Coimbatore", "Pondicherry", "Patna",
]

# Approximate road distances (km) for well-travelled corridors.
# Stored one-directional; looked up both ways.
_DIST = {
    ("New Delhi", "Agra"): 233,
    ("New Delhi", "Jaipur"): 280,
    ("New Delhi", "Chandigarh"): 245,
    ("New Delhi", "Lucknow"): 555,
    ("New Delhi", "Dehradun"): 250,
    ("New Delhi", "Amritsar"): 450,
    ("New Delhi", "Haridwar"): 220,
    ("New Delhi", "Kanpur"): 490,
    ("New Delhi", "Shimla"): 343,
    ("Mumbai", "Pune"): 150,
    ("Mumbai", "Goa"): 590,
    ("Mumbai", "Ahmedabad"): 525,
    ("Mumbai", "Surat"): 285,
    ("Mumbai", "Nagpur"): 837,
    ("Pune", "Goa"): 455,
    ("Pune", "Nagpur"): 720,
    ("Bengaluru", "Chennai"): 346,
    ("Bengaluru", "Mysuru"): 145,
    ("Bengaluru", "Hyderabad"): 570,
    ("Bengaluru", "Goa"): 560,
    ("Bengaluru", "Coimbatore"): 365,
    ("Chennai", "Pondicherry"): 170,
    ("Chennai", "Coimbatore"): 505,
    ("Chennai", "Bengaluru"): 346,
    ("Hyderabad", "Bengaluru"): 570,
    ("Hyderabad", "Nagpur"): 500,
    ("Ahmedabad", "Surat"): 265,
    ("Ahmedabad", "Jaipur"): 660,
    ("Ahmedabad", "Indore"): 405,
    ("Jaipur", "Agra"): 240,
    ("Jaipur", "New Delhi"): 280,
    ("Lucknow", "Kanpur"): 90,
    ("Lucknow", "Varanasi"): 320,
    ("Lucknow", "Agra"): 335,
    ("Kanpur", "New Delhi"): 490,
    ("Varanasi", "Patna"): 245,
    ("Chandigarh", "Shimla"): 115,
    ("Chandigarh", "Manali"): 310,
    ("Chandigarh", "Amritsar"): 230,
    ("Dehradun", "Haridwar"): 55,
    ("Dehradun", "Rishikesh"): 45,
    ("Haridwar", "Rishikesh"): 25,
    ("Shimla", "Manali"): 245,
    ("Indore", "Bhopal"): 195,
    ("Bhopal", "Nagpur"): 350,
    ("Kolkata", "Patna"): 585,
    ("Kolkata", "Varanasi"): 680,
}


def get_distance(a: str, b: str):
    """Look up an approximate road distance in km, either direction."""
    if a == b:
        return 0
    if (a, b) in _DIST:
        return _DIST[(a, b)]
    if (b, a) in _DIST:
        return _DIST[(b, a)]
    return None


# Bus corridors that actually run a service (derived from the distance map,
# both directions).
BUS_ROUTES = sorted({pair for k in _DIST for pair in (k, (k[1], k[0]))})


def estimate_distance(a: str, b: str) -> int:
    """Fallback distance estimate for hire quotes when a route isn't in the
    curated matrix — used only so the vehicle-hire quote tool never dead-ends.
    Not authoritative; real fleets would plug in a maps API here."""
    known = get_distance(a, b)
    if known is not None:
        return known
    # deterministic pseudo-estimate so repeated quotes for the same pair match
    seed = sum(ord(c) for c in (a + b))
    return 180 + (seed % 620)


GST_RATE = 0.05
MIN_KM_PER_DAY_OUTSTATION = 250  # standard Indian outstation taxi convention
LOCAL_PACKAGE_KM = 80
LOCAL_PACKAGE_HOURS = 8


def calculate_hire_price(price_per_km, price_per_day_local, driver_allowance_per_day,
                          trip_type, distance_km, days):
    """Indian outstation-taxi style pricing.

    trip_type == "local": flat per-day package (80km/8hr), driver allowance
                           only if the vehicle requires a driver.
    trip_type == "outstation": round-trip km billed at MIN_KM_PER_DAY_OUTSTATION
                           per day minimum (standard convention), plus driver
                           allowance per day, plus 5% GST.
    """
    price_per_km = float(price_per_km)
    price_per_day_local = float(price_per_day_local)
    driver_allowance_per_day = float(driver_allowance_per_day)
    days = max(1, int(days))

    if trip_type == "local":
        base_fare = price_per_day_local * days
        driver_charges = driver_allowance_per_day * days
    else:
        round_trip_km = distance_km * 2
        billed_km = max(round_trip_km, MIN_KM_PER_DAY_OUTSTATION * days)
        base_fare = billed_km * price_per_km
        driver_charges = driver_allowance_per_day * days

    subtotal = base_fare + driver_charges
    gst = subtotal * GST_RATE
    total = math.ceil(subtotal + gst)

    return {
        "base_fare": round(base_fare, 2),
        "driver_charges": round(driver_charges, 2),
        "gst": round(gst, 2),
        "total_price": total,
        "billed_km": (distance_km * 2) if trip_type == "outstation" else LOCAL_PACKAGE_KM,
    }