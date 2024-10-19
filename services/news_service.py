import requests
import pandas as pd

# Base API URL
base_url = "https://api-berita-indonesia.vercel.app"

# List of routes and their corresponding categories
routes = {
    "sindonews": ["ekbis", "international"],
    "tempo": ["bisnis"],
    "antara": ["politik"],
    "cnn": ["internasional"]
}

# Function to fetch data from a specific route and category
def fetch_data(route, category):
    url = f"{base_url}/{route}/{category}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Return JSON data if the request is successful
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error for {route}/{category}: {e}")
    except Exception as e:
        print(f"Error for {route}/{category}: {e}")
    return None

# Function to fetch news and return combined results
def get_combined_news():
    combined_results = []

    # Loop through each route and its categories to fetch data
    for route, categories in routes.items():
        for category in categories:
            data = fetch_data(route, category)
            if data and data.get('success'):
                posts = data['data'].get('posts', [])
                for post in posts:
                    combined_results.append({
                        'Title': post.get('title', 'No Title'),
                        'Description': post.get('description', 'No Description'),
                        'Publication Date': post.get('pubDate', 'No Date'),
                        'Source': f"{route.capitalize()} - {category.capitalize()}",
                        'Link': post.get('link', '#'),
                        'Image': post.get('thumbnail', '')  # Use the thumbnail URL directly
                    })

    # Convert to DataFrame
    combined_df = pd.DataFrame(combined_results)

    # Ensure all necessary columns are present
    for col in ['Title', 'Description', 'Publication Date', 'Source', 'Link', 'Image']:
        if col not in combined_df.columns:
            combined_df[col] = 'N/A'

    # Ensure date is in string format
    combined_df['Publication Date'] = combined_df['Publication Date'].astype(str)

    return combined_df
