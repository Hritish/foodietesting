import streamlit as st
import requests
import random
import geocoder
import folium
from streamlit_folium import folium_static
from db import SessionLocal, SavedRestaurant
from auth import login_user, register_user

# Initialize DB session
db = SessionLocal()

# Yelp API Key
yelp_api_key = "YOUR_YELP_API_KEY"

# **Northeast US Cities and Their Iconic Dishes**
northeast_city_food_map = {
    "New York City, NY": ("Pizza", (40.7128, -74.0060)),
    "Philadelphia, PA": ("Cheesesteak", (39.9526, -75.1652)),
    "Boston, MA": ("Clam Chowder", (42.3601, -71.0589)),
    "Buffalo, NY": ("Buffalo Wings", (42.8864, -78.8784)),
    "Providence, RI": ("Stuffies", (41.8236, -71.4222)),
    "Portland, ME": ("Lobster Rolls", (43.6591, -70.2568)),
    "Baltimore, MD": ("Crab Cakes", (39.2904, -76.6122)),
    "New Haven, CT": ("Pizza", (41.3083, -72.9279)),
    "Jersey City, NJ": ("Bagels", (40.7178, -74.0431))
}

cuisines_list = ["N/A", "American", "Chinese", "Mexican", "Italian", "Japanese", "Indian", "Thai",
                 "Mediterranean", "French", "Greek", "Korean", "Vietnamese", "Spanish", "Brazilian",
                 "Middle Eastern", "Other"]

dietary_options = ["N/A", "Vegetarian", "Gluten-Free", "Vegan", "Kosher", "Halal", "Other"]

# --- TITLE ---
st.title("🍽️ Foodie - Find Your Perfect Meal!")

# --- AUTH SIDEBAR ---
st.sidebar.header("🔐 Account")

if "user" not in st.session_state:
    st.session_state.user = None

auth_mode = st.sidebar.radio("Login or Register:", ["Login", "Register"])
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Submit"):
    if auth_mode == "Register":
        result = register_user(db, username, password)
        st.sidebar.success(result)
    else:
        user = login_user(db, username, password)
        if user:
            st.session_state.user = user
            st.sidebar.success(f"Logged in as {user.username}")
        else:
            st.sidebar.error("Login failed")

# --- SEARCH OPTIONS ---
st.sidebar.header("🔍 Search Settings")

selected_city = st.sidebar.selectbox("🏙️ Explore a City?", ["N/A"] + list(northeast_city_food_map.keys()))

if selected_city != "N/A":
    st.sidebar.write(f"🍽️ {selected_city} is known for: **{northeast_city_food_map[selected_city][0]}**")
    search_location = selected_city
    map_center = northeast_city_food_map[selected_city][1]
    disable_address_input = True
else:
    search_location = st.sidebar.text_input("📍 Enter address or ZIP code:")
    map_center = None
    disable_address_input = False

distance_unit = st.sidebar.selectbox("📏 Distance Unit:", ["miles", "feet"])
distance = st.sidebar.slider("🛣️ Distance:", 0, 15 if distance_unit == "miles" else 2500,
                             5 if distance_unit == "miles" else 500)

dietary_selection = st.sidebar.selectbox("🥗 Dietary Restrictions:", dietary_options)
dietary_restrictions = None if dietary_selection == "N/A" else [dietary_selection] if dietary_selection != "Other" else \
    st.sidebar.text_input("Enter your dietary restrictions:").split(",")

budget_map = {"Cheap": 1, "Moderate": 2, "Expensive": 3, "Luxury": 4}
budget = st.sidebar.selectbox("💰 Budget:", list(budget_map.keys()), index=1)

cuisine = st.sidebar.selectbox("🍽️ Preferred cuisine:", cuisines_list)
if selected_city != "N/A":
    cuisine = northeast_city_food_map[selected_city][0]

# --- SEARCH FUNCTION ---
def get_restaurants():
    global map_center

    if selected_city == "N/A":
        g = geocoder.arcgis(search_location)
        if not g.latlng:
            st.error("Invalid location.")
            return None, None
        user_location = g.latlng
        map_center = user_location
    else:
        user_location = None

    max_radius_meters = min(int(distance * (1609.34 if distance_unit == 'miles' else 0.3048)), 40000)

    headers = {"Authorization": f"Bearer {yelp_api_key}"}
    params = {
        "location": search_location,
        "limit": 50,
        "radius": max_radius_meters,
        "price": budget_map[budget]
    }

    if cuisine:
        params["categories"] = cuisine.lower().replace(" ", "_")
        params["term"] = cuisine

    if dietary_restrictions:
        params["term"] += f", {', '.join(dietary_restrictions)}"

    response = requests.get("https://api.yelp.com/v3/businesses/search", headers=headers, params=params)
    if response.status_code != 200:
        st.error("Yelp API Error")
        return None, None

    data = response.json().get("businesses", [])

    blocked_categories = {
        "liquorstores", "wineries", "breweries", "distilleries",
        "hair", "barbers", "massage", "spas", "tattooshops",
        "nail_salons", "tanning", "piercing", "gyms"
    }

    filtered = []
    for b in data:
        cats = {cat["alias"] for cat in b.get("categories", [])}
        if cats.intersection(blocked_categories):
            continue

        filtered.append((
            b["id"], b["name"], ", ".join(b["location"].get("display_address", [])),
            b.get("display_phone", "N/A"),
            ", ".join([cat["title"] for cat in b.get("categories", [])]),
            [b["coordinates"]["latitude"], b["coordinates"]["longitude"]],
            b.get("image_url", ""), round(b["distance"] * 3.28084),
            b.get("url", "#")
        ))

    random.shuffle(filtered)
    return filtered, filtered[:3] if len(filtered) >= 3 else filtered

# --- SEARCH BUTTON ---
if st.sidebar.button("🔍 Find Restaurants"):
    with st.spinner("Searching..."):
        restaurants, top_picks = get_restaurants()

    if not restaurants:
        st.error("No restaurants found.")
    else:
        tab1, tab2 = st.tabs(["📋 List View", "🗺️ Map View"])

        with tab1:
            st.header("🍴 Top Picks")
            for r in top_picks:
                with st.container():
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        st.image(r[6], width=150)

                    with col2:
                        st.markdown(f"### {r[1]}")
                        st.write(f"📍 **Address:** {r[2]}")
                        st.write(f"📞 **Phone:** {r[3]}")
                        st.write(f"🍽️ **Categories:** {r[4]}")
                        st.markdown(f"[🔗 Visit Website]({r[8]})", unsafe_allow_html=True)

                        popularity = random.randint(60, 98)
                        st.progress(popularity / 100)
                        st.write(f"🔥 Popularity Score: **{popularity}%**")

                        # Save button
                        if st.session_state.user:
                            if st.button("💾 Save", key=r[0]):
                                exists = db.query(SavedRestaurant).filter_by(user_id=st.session_state.user.id, yelp_id=r[0]).first()
                                if not exists:
                                    db.add(SavedRestaurant(user_id=st.session_state.user.id, yelp_id=r[0], name=r[1], image_url=r[6], url=r[8]))
                                    db.commit()
                                    st.success("Saved!")
                        else:
                            st.info("Login to save this restaurant")

        with tab2:
            st.header("🗺️ Map View")
            if map_center:
                m = folium.Map(location=map_center, zoom_start=13)
                folium.Marker(location=map_center, icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)

                for r in top_picks:
                    folium.Marker(
                        location=r[5],
                        popup=f'<b>{r[1]}</b><br><a href="{r[8]}" target="_blank">Visit Yelp Page</a>',
                        icon=folium.Icon(color="red", icon="cutlery")
                    ).add_to(m)

                folium_static(m)

# --- SAVED RESTAURANTS ---
if st.session_state.user:
    st.header("❤️ My Saved Restaurants")
    saved = db.query(SavedRestaurant).filter_by(user_id=st.session_state.user.id).all()
    if saved:
        for r in saved:
            with st.container():
                st.image(r.image_url, width=100)
                st.markdown(f"### {r.name}")
                st.markdown(f"[🔗 Visit Website]({r.url})", unsafe_allow_html=True)
    else:
        st.info("No saved restaurants yet.")
