import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from appointments.models import Appointment
from users.models import KrisshakProfile, BhooswamiProfile

def get_krisshak_recommendations(bhooswami):
    """Suggests Krisshaks based on past appointments, expertise, and district."""
    
    # Fetch previous appointments for Bhooswami
    previous_krisshaks = Appointment.objects.filter(
        bhooswami=bhooswami.user, status="confirmed"
    ).values_list("krisshak_id", flat=True)

    # Get all Krisshaks from the same district
    district_krisshaks = KrisshakProfile.objects.filter(district=bhooswami.district)

    # Create DataFrame for ML processing
    data = [
        {
            "krisshak_id": krisshak.id,
            "ratings": krisshak.ratings,
            "specialization": krisshak.specialization,
            "previously_appointed": 1 if krisshak.id in previous_krisshaks else 0,
            "matches_required_crops": 1 if bhooswami.requirements and bhooswami.requirements in (krisshak.specialization or "") else 0,
        }
        for krisshak in district_krisshaks
    ]

    df = pd.DataFrame(data)

    # Train K-Nearest Neighbors model
    model = KNeighborsClassifier(n_neighbors=3)
    X = df[["ratings", "previously_appointed", "matches_required_crops"]]
    y = df["krisshak_id"]
    model.fit(X, y)

    # Predict for the **specific Bhooswami request**, not the entire dataset
    user_input = [[bhooswami.ratings, 1, 1]]  # Simulating user query
    recommendations = model.predict(user_input)

    return KrisshakProfile.objects.filter(id__in=recommendations).order_by("-ratings", "-previously_appointed")


def get_bhooswami_recommendations(krisshak):
    """Suggests Bhooswamis based on previous appointments, expertise, and specialization."""
    
    previous_bhooswamis = Appointment.objects.filter(
        krisshak=krisshak, status="confirmed"
    ).values_list("bhooswami_id", flat=True)

    district_bhooswamis = BhooswamiProfile.objects.filter(district=krisshak.district)

    data = [
        {
            "bhooswami_id": bhooswami.id,
            "ratings": bhooswami.ratings,
            "requirements": bhooswami.requirements,
            "previously_appointed": 1 if bhooswami.id in previous_bhooswamis else 0,
            "matches_specialization": 1 if krisshak.specialization in bhooswami.requirements else 0,
        }
        for bhooswami in district_bhooswamis
    ]

    df = pd.DataFrame(data)

    model = KNeighborsClassifier(n_neighbors=3)
    X = df[["ratings", "previously_appointed", "matches_specialization"]]
    y = df["bhooswami_id"]
    model.fit(X, y)

    # Predict for the **specific Krisshak request**, not the entire dataset
    user_input = [[krisshak.ratings, 1, 1]]  # Simulating user query
    recommendations = model.predict(user_input)

    return BhooswamiProfile.objects.filter(id__in=recommendations).order_by("-ratings", "-previously_appointed")