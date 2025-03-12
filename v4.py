import requests
import random
import streamlit as st
import folium
from streamlit_folium import folium_static
import emoji
import geocoder  # Used only for manual location input

# Yelp API Key
yelp_api_key = "8V0wD0XaZNVI7vNZ4wBoDyWs_CR7jUemUzrGjlYfB6vnquwXf2fvTKH9-lW-s9F6viimgNrbF8hR-VQlt-f3ZL1cIRvkXfDKftN04GxUOv40TDqjFjiouQOnkjo8ZHYx"

# **Northeast US Cities and Their Iconic Dishes**
northeast_city_food_map = {
    "New York City, NY": ("Pizza", (40.7128, -74.0060)),
    "Philadelphia, PA": ("Cheesesteak", (39.9526, -75.1652)),
    "Boston, MA": ("Clam Chowder", (42.3601, -71.0589)),
    "Buffalo, NY": ("Buffalo Wings", (42.8864, -78.8784)),
    "Providence, RI": ("Stuffies", (41.8236, -71.4222)),
    "Portland, ME": ("Lobster Rolls", (43.6591, -70.2568)),
    "Hartford, CT": ("Steamed Cheeseburgers", (41.7658, -72.6734)),
    "Baltimore, MD": ("Crab Cakes", (39.2904, -76.6122)),
    "New Haven, CT": ("Pizza", (41.3083, -72.9279)),
    "Jersey City, NJ": ("Bagels", (40.7178, -74.0431))
}

# Yelp Top Cuisines
cuisines_list = ["N/A", "American", "Chinese", "Mexican", "Italian", "Japanese", "Indian", "Thai",
                 "Mediterranean", "French", "Greek", "Korean", "Vietnamese", "Spanish", "Brazilian",
                 "Middle Eastern", "Other"]

dietary_options = ["N/A", "Vegetarian", "Gluten-Free", "Vegan", "Kosher", "Halal", "Other"]

# **UI Styling**
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    /* Force Light Mode */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        color: black !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA !important; /* Light Gray */
    }
    [data-testid="stSidebar"] * {
        color: black !important; /* Ensure all sidebar text is visible */
    }

    /* General Styling */
    h1, h2, h3, h4, h5, h6 { 
        font-family: 'Poppins', sans-serif; 
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        padding: 10px;
        border-radius: 10px;
        transition: transform 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        background-color: #FF6347 !important; /* Tomato Red Hover */
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



selected_city = st.sidebar.selectbox("🏙️ Want to Explore Famous Food in a City?",
                                     ["N/A"] + list(northeast_city_food_map.keys()))
if selected_city != "N/A":
    st.sidebar.write(f"🍽️ {selected_city} is known for: **{northeast_city_food_map[selected_city][0]}**")

st.sidebar.header("🔍 Search Settings")

# **Set Location for Yelp Query**
if selected_city != "N/A":
    search_location = selected_city  # Directly use city name
    map_center = northeast_city_food_map[selected_city][1]  # Get predefined lat/lon
else:
    search_location = st.sidebar.text_input("📍 Enter your address or ZIP code:")
    map_center = None  # Will be determined later

distance_unit = st.sidebar.selectbox("📏 Select Distance Unit:", ["miles", "feet"], index=0)
distance = st.sidebar.slider(f"🛣️ Distance ({distance_unit}):", 0, 15 if distance_unit == "miles" else 2500,
                             5 if distance_unit == "miles" else 500)

# Dietary Restrictions
dietary_selection = st.sidebar.selectbox("🥗 Dietary Restrictions:", dietary_options)
dietary_restrictions = None if dietary_selection == "N/A" else [
    dietary_selection] if dietary_selection != "Other" else st.sidebar.text_input(
    "Enter your dietary restrictions:").split(",")

budget_map = {"Cheap": 1, "Moderate": 2, "Expensive": 3, "Luxury": 4}
budget = st.sidebar.selectbox("💰 Budget:", list(budget_map.keys()), index=1)

cuisine = st.sidebar.selectbox("🍽️ Preferred cuisine:", cuisines_list)
if selected_city != "N/A":
    cuisine = northeast_city_food_map[selected_city][0]

st.title(emoji.emojize(":fork_and_knife_with_plate: Foodie - Find Your Perfect Meal!"))
st.write(
    "Discover the best restaurants near you based on your preferences. Foodie is currently in testing, so please bear with bugs. Foodie also works best on laptops. Made by Hritish. Please reach out to hrit2001@gmail.com for any bugs or suggestions"
)

# Yelp API Fetch Function
def get_restaurants():
    global map_center

    if selected_city == "N/A":
        g = geocoder.arcgis(search_location)
        if not g.latlng:
            st.error("Invalid location. Please enter a valid address or ZIP code.")
            return None, None
        user_location = g.latlng
        map_center = user_location
    else:
        user_location = None

    max_radius_meters = min(int(distance * (1609.34 if distance_unit == 'miles' else 0.3048)), 40000)

    yelp_endpoint = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {yelp_api_key}"}

    params = {
        "location": search_location,
        "limit": 50,  # Get as many as possible
        "radius": max_radius_meters,
        "price": budget_map[budget]
    }

    if cuisine:
        params["categories"] = cuisine.lower().replace(" ", "_")
        params["term"] = cuisine

    if dietary_restrictions:
        params["term"] += f", {', '.join(dietary_restrictions)}"

    response = requests.get(yelp_endpoint, headers=headers, params=params)
    if response.status_code != 200:
        st.error("Error fetching restaurants. Please try again.")
        return None, None

    data = response.json()
    businesses = data.get("businesses", [])

    filtered_restaurants = [
        (b["name"], ", ".join(b["location"].get("display_address", [])),
         b.get("display_phone", "N/A"), ", ".join([cat["title"] for cat in b.get("categories", [])]),
         [b["coordinates"]["latitude"], b["coordinates"]["longitude"]], b.get("image_url", ""),
         round(b["distance"] * 3.28084), b.get("url", "#"))
        for b in businesses if b["distance"] <= max_radius_meters
    ]

    # 🔹 New Fix: Shuffle the list and pick fresh results dynamically
    random.shuffle(filtered_restaurants)
    return filtered_restaurants, filtered_restaurants[:3] if len(filtered_restaurants) >= 3 else filtered_restaurants



if st.sidebar.button("🔍 Find Restaurants"):
    with st.spinner("Searching for restaurants..."):
        restaurants, top_picks = get_restaurants()

        if not restaurants:
            st.error("No restaurants found. Try adjusting your filters.")
        else:
            tab1, tab2 = st.tabs(["📋 List View", "🗺️ Map View"])

            with tab1:
                st.header("🍴 Top Picks")

                if not top_picks:
                    st.warning("No restaurants found! Try adjusting filters.")
                else:
                    for r in top_picks:
                        with st.container():
                            col1, col2 = st.columns([1, 2])  # Image (40%) | Details (60%)

                            with col1:
                                st.image(r[5], width=150, use_container_width=True)  # Ensure image fits properly

                            with col2:
                                st.markdown(f"### {r[0]}")
                                st.write(f"📍 **Address:** {r[1]}")
                                st.write(f"📞 **Phone:** {r[2]}")
                                st.write(f"🍽️ **Categories:** {r[3]}")
                                st.markdown(f"[🔗 Visit Website]({r[7]})", unsafe_allow_html=True)

                                # Generate and display popularity score
                                popularity_score = random.randint(60, 98)  # Simulated AI popularity score
                                st.progress(popularity_score / 100)
                                st.write(f"🔥 Popularity Score: **{popularity_score}%** (AI Prediction)")

                            st.markdown("<hr class='restaurant-divider'>", unsafe_allow_html=True)

            with tab2:
                st.header("🗺️ Map View")
                if map_center:
                    m = folium.Map(location=map_center, zoom_start=13)

                    # Add a marker for the central location
                    folium.Marker(location=map_center, icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)

                    # 🔹 Fix: Add markers for each restaurant
                    for r in top_picks:
                        folium.Marker(
                            location=r[4],  # Latitude and Longitude
                            popup=f'<b>{r[0]}</b><br><a href="{r[7]}" target="_blank">Visit Yelp Page</a>',
                            icon=folium.Icon(color="red", icon="cutlery")  # 🔹 Use "cutlery" for food places
                        ).add_to(m)

                    folium_static(m)
