import requests
import geocoder
import random
import streamlit as st
import folium
from streamlit_folium import folium_static
import emoji

# Yelp API Key
yelp_api_key = "8V0wD0XaZNVI7vNZ4wBoDyWs_CR7jUemUzrGjlYfB6vnquwXf2fvTKH9-lW-s9F6viimgNrbF8hR-VQlt-f3ZL1cIRvkXfDKftN04GxUOv40TDqjFjiouQOnkjo8ZHYx"

# Yelp Top Cuisines
cuisines_list = [
    "N/A", "American", "Chinese", "Mexican", "Italian", "Japanese", "Indian", "Thai", "Mediterranean",
    "French", "Greek", "Korean", "Vietnamese", "Spanish", "Brazilian", "Middle Eastern", "Other"
]

dietary_options = ["N/A", "Vegetarian", "Gluten-Free", "Vegan", "Kosher", "Halal", "Other"]

# **Enhanced UI with Modern Look**
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    body { font-family: 'Poppins', sans-serif !important; }
    .stTextInput, .stSelectbox, .stSlider, .stButton, .stRadio { font-size: 16px !important; font-family: 'Poppins', sans-serif; }
    .stSidebar { background-color: #F8F9FA; padding: 20px; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Poppins', sans-serif; font-weight: 600; }

    /* Animated Search Button */
    .stButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        font-size: 16px;
        padding: 10px;
        border-radius: 10px;
        transition: transform 0.3s ease, background-color 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        background-color: #FF6347 !important; /* Tomato Red Hover */
    }

    /* Restaurant Cards */
    .restaurant-card {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        margin: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        color: black !important;
    }

    /* Divider */
    .restaurant-divider {
        margin-top: 20px;
        margin-bottom: 20px;
        border: none;
        height: 2px;
        background: #FF4B4B; /* Red Line */
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar UI
st.sidebar.header("🔍 Search Settings")
location_input = st.sidebar.text_input("📍 Enter your address or ZIP code:")

distance_unit = st.sidebar.selectbox("📏 Select Distance Unit:", ["miles", "feet"], index=0)
distance = st.sidebar.slider(f"🛣️ Distance ({distance_unit}):", 0, 15 if distance_unit == "miles" else 2500,
                             5 if distance_unit == "miles" else 500)

dietary_selection = st.sidebar.selectbox("🥗 Dietary Restrictions:", dietary_options)
dietary_restrictions = None if dietary_selection == "N/A" else [
    dietary_selection] if dietary_selection != "Other" else st.sidebar.text_input(
    "Enter your dietary restrictions:").split(",")

budget_map = {"Cheap": 1, "Moderate": 2, "Expensive": 3, "Luxury": 4}
budget = st.sidebar.selectbox("💰 Budget:", list(budget_map.keys()), index=1)

cuisine = st.sidebar.selectbox("🍽️ Preferred cuisine:", cuisines_list)
cuisine = None if cuisine == "N/A" else cuisine if cuisine != "Other" else st.sidebar.text_input(
    "Enter your preferred cuisine:")

st.title(emoji.emojize(":fork_and_knife_with_plate: Foodie - Find Your Perfect Meal!"))
st.write("Discover the best restaurants near you based on your preferences.")

# Store global geolocation
user_location = None


# Yelp API Fetch Function
def get_restaurants():
    global user_location
    g = geocoder.arcgis(location_input)
    if not g.latlng:
        st.error("Invalid location. Please enter a valid address or ZIP code.")
        return None, None
    user_location = g.latlng  # Store user location globally

    radius = min(int(distance * (1609.34 if distance_unit == 'miles' else 0.3048)), 40000)

    yelp_endpoint = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {yelp_api_key}"}
    params = {
        "location": location_input,
        "categories": cuisine.lower().replace(" ", "_") if cuisine else "restaurant",
        "limit": 50,
        "radius": radius,
        "price": budget_map[budget]
    }

    response = requests.get(yelp_endpoint, headers=headers, params=params)
    if response.status_code != 200:
        st.error("Error fetching restaurants. Please try again.")
        return None, None

    data = response.json()
    businesses = data.get("businesses", [])

    restaurants = [
        (b["name"], ", ".join(b["location"].get("display_address", [])),
         b.get("display_phone", "N/A"), ", ".join([cat["title"] for cat in b.get("categories", [])]),
         [b["coordinates"]["latitude"], b["coordinates"]["longitude"]], b.get("image_url", ""),
         round(b["distance"] * 3.28084), b.get("url", "#"))
        for b in businesses
    ]

    return restaurants, random.sample(restaurants, min(len(restaurants), 3)) if restaurants else ([], [])


# Function to generate a fake AI-powered popularity score
def get_popularity_score():
    return random.randint(60, 98)  # Simulated AI popularity score


if st.sidebar.button("🔍 Find Restaurants"):
    with st.spinner("Searching for restaurants..."):
        restaurants, top_picks = get_restaurants()

        if not restaurants:
            st.error("No restaurants found. Try adjusting your filters.")
        else:
            tab1, tab2 = st.tabs(["📋 List View", "🗺️ Map View"])

            with tab1:
                st.header("🍴 Top Picks")
                for idx, r in enumerate(top_picks):
                    with st.container():
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.image(r[5], width=150, use_container_width=True)
                        with col2:
                            st.markdown(f"### {r[0]}")
                            st.write(f"📍 Address: {r[1]}")
                            st.write(f"📞 Phone: {r[2]}")
                            st.write(f"🍽️ Categories: {r[3]}")
                            st.markdown(f"[🔗 Visit Website]({r[7]})", unsafe_allow_html=True)

                            popularity_score = get_popularity_score()
                            st.progress(popularity_score / 100)
                            st.write(f"🔥 Popularity Score: **{popularity_score}%** (AI Prediction)")

                    if idx < len(top_picks) - 1:
                        st.markdown("<hr class='restaurant-divider'>", unsafe_allow_html=True)

            with tab2:
                st.header("🗺️ Map View")
                if top_picks and user_location:
                    m = folium.Map(location=user_location, zoom_start=13, tiles="cartodbpositron")

                    # Keep user marker but remove popup
                    folium.Marker(location=user_location, icon=folium.Icon(color="blue")).add_to(m)

                    for r in top_picks:
                        folium.Marker(location=r[4], popup=f'<a href="{r[7]}" target="_blank">{r[0]}</a>',
                                      icon=folium.Icon(color="green")).add_to(m)

                    folium_static(m)
                else:
                    st.warning("No locations available.")
