import requests
import json
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
    "American", "Chinese", "Mexican", "Italian", "Japanese", "Indian", "Thai", "Mediterranean",
    "French", "Greek", "Korean", "Vietnamese", "Spanish", "Brazilian", "Middle Eastern", "Other"
]

dietary_options = ["Vegetarian", "Gluten-Free", "Vegan", "Kosher", "Halal", "Other"]

def get_restaurants(location_input, dietary_restrictions=None, budget=None, distance=None, distance_unit='miles', cuisine=None, min_rating=None):
    g = geocoder.arcgis(location_input)
    if not g.latlng:
        st.error("Invalid location. Please enter a valid address or ZIP code.")
        return None, None
    location = f"{g.latlng[0]},{g.latlng[1]}"

    # Convert distance to meters
    if distance_unit == 'feet':
        radius = min(int(distance * 0.3048), 40000)
    else:
        radius = min(int(distance * 1609.34), 40000)

    yelp_endpoint = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {yelp_api_key}"}
    params = {
        "location": location_input,
        "categories": cuisine.lower().replace(" ", "_"),
        "limit": 50,
        "radius": radius,
    }

    if dietary_restrictions:
        params["term"] = ",".join(dietary_restrictions)
    if budget:
        params["price"] = budget
    if cuisine and cuisine != "Other":
        params["term"] = cuisine

    response = requests.get(yelp_endpoint, headers=headers, params=params)
    if response.status_code != 200:
        st.error("Error fetching restaurants. Please try again.")
        return None, None

    data = response.json()
    businesses = data.get("businesses", [])
    restaurants = []

    for business in businesses:
        name = business["name"]
        rating = business["rating"]
        if min_rating and rating < min_rating:
            continue
        distance_m = business["distance"]
        distance_ft = round(distance_m * 3.28084)
        address = ", ".join(business["location"].get("display_address", []))
        phone = business.get("display_phone", "N/A")
        categories = ", ".join([cat["title"] for cat in business.get("categories", [])])
        coordinates = [business["coordinates"]["latitude"], business["coordinates"]["longitude"]]
        image_url = business.get("image_url", "")

        restaurants.append((name, rating, address, phone, categories, coordinates, image_url, distance_ft))

    return restaurants, random.sample(restaurants, min(len(restaurants), 3))

# Sidebar UI
st.sidebar.header("Search Settings")
location_input = st.sidebar.text_input("Enter your address or ZIP code:")

distance_unit = st.sidebar.selectbox("Select Distance Unit:", ["miles", "feet"], index=0)

if distance_unit == "miles":
    distance = st.sidebar.slider("Distance (miles):", 0, 15, 5)
else:
    distance = st.sidebar.slider("Distance (feet):", 0, 2500, 500, step=100)

dietary_selection = st.sidebar.selectbox("Dietary Restrictions:", dietary_options)
if dietary_selection == "Other":
    dietary_restrictions = st.sidebar.text_input("Enter your dietary restrictions:")
    dietary_restrictions = [x.strip() for x in dietary_restrictions.split(",") if dietary_restrictions]
else:
    dietary_restrictions = [dietary_selection]

budget = st.sidebar.selectbox("Budget:", ["Cheap", "Moderate", "Expensive", "Luxury"], index=1)
budget_map = {"Cheap": 1, "Moderate": 2, "Expensive": 3, "Luxury": 4}
selected_budget = budget_map[budget]

cuisine = st.sidebar.selectbox("Preferred cuisine:", cuisines_list)
if cuisine == "Other":
    cuisine = st.sidebar.text_input("Enter your preferred cuisine:")

min_rating = st.sidebar.slider("Minimum Rating:", 1.0, 5.0, 4.0, step=0.5)

if "selected_restaurant" not in st.session_state:
    st.session_state.selected_restaurant = None

st.title(emoji.emojize("Welcome to Foodie :fork_and_knife_with_plate:"))
st.write("Discover the best restaurants near you based on your preferences.")

if st.sidebar.button("Find Restaurants"):
    with st.spinner("Searching for restaurants..."):
        restaurants, top_picks = get_restaurants(location_input, dietary_restrictions, selected_budget, distance, distance_unit, cuisine, min_rating)
        if not restaurants:
            st.error("No restaurants found. Please try adjusting your filters.")
        else:
            st.header("Top Picks")
            for index, restaurant in enumerate(top_picks):
                st.image(restaurant[6], width=300, caption=restaurant[0])
                st.markdown(f"**{restaurant[0]}**")
                st.write(f"Rating: {restaurant[1]} stars")
                st.write(f"Address: {restaurant[2]}")
                st.write(f"Phone: {restaurant[3]}")
                st.write(f"Categories: {restaurant[4]}")
                st.write(f"Distance: {restaurant[7]} ft")

            # Display map
            st.header("Map View")
            g = geocoder.arcgis(location_input)
            if g.latlng:
                m = folium.Map(location=[g.latlng[0], g.latlng[1]], zoom_start=13)
                folium.Marker(location=[g.latlng[0], g.latlng[1]], popup="You are here", icon=folium.Icon(color="blue")).add_to(m)
                for restaurant in top_picks:
                    folium.Marker(location=restaurant[5], popup=restaurant[0], icon=folium.Icon(color="green")).add_to(m)
                folium_static(m)
