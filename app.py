import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Local Food Wastage Management System", layout="wide")
DB_FILE = "food_wastage.db"

def run_query(query):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            return pd.read_sql_query(query, conn)
    except Exception as e:
        return pd.DataFrame({"Error Running Query": [str(e)]})

# Helper function to auto-detect matching column names dynamically
def find_best_column(table_name, keywords, fallback_index=0):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1", conn)
            cols = list(df.columns)
            # Search for keyword matches in column names
            for kw in keywords:
                for col in cols:
                    if kw.lower() in col.lower():
                        return col
            # Fallback to positional column if no matching keyword string is found
            if fallback_index < len(cols):
                return cols[fallback_index]
            return cols[0]
    except:
        return f"c{fallback_index + 1}"

st.title("🌱 Local Food Wastage Management System")
st.markdown("### Connecting surplus food providers with local individuals and NGOs to reduce waste.")
st.write("---")

menu = st.sidebar.radio("Navigation Menu", ["📊 Live Dashboard & Filters", "🔍 15 Business SQL Queries"])

# --- Auto-detecting your real database column structure safely ---
prov_city = find_best_column("providers_data", ["city", "location", "c5"], 4)
prov_type = find_best_column("providers_data", ["type", "c3"], 2)
prov_id = find_best_column("providers_data", ["id", "c1"], 0)
prov_name = find_best_column("providers_data", ["name", "c2"], 1)

recv_city = find_best_column("receivers_data", ["city", "location", "c4"], 3)
recv_type = find_best_column("receivers_data", ["type", "c3"], 2)
recv_id = find_best_column("receivers_data", ["id", "c1"], 0)
recv_name = find_best_column("receivers_data", ["name", "c2"], 1)

food_qty = find_best_column("food_listings_data", ["qty", "quantity", "c3"], 2)
food_item = find_best_column("food_listings_data", ["item", "name", "food", "c2"], 1)
food_prov_fk = find_best_column("food_listings_data", ["prov", "c5"], 4)
food_loc = find_best_column("food_listings_data", ["loc", "city", "c7"], 6)
food_meal = find_best_column("food_listings_data", ["meal", "c9"], 8)
food_id = find_best_column("food_listings_data", ["id", "c1"], 0)
food_type = find_best_column("food_listings_data", ["type", "c8"], 7)

claim_status = find_best_column("claims_data", ["status", "state", "c4"], 3)
claim_id = find_best_column("claims_data", ["id", "c1"], 0)
claim_food_fk = find_best_column("claims_data", ["food", "c2"], 1)
claim_recv_fk = find_best_column("claims_data", ["recv", "user", "c3"], 2)

# ====================================================================
# TAB 1: LIVE DASHBOARD
# ====================================================================
if menu == "📊 Live Dashboard & Filters":
    st.header("🛒 Current Available Food Listings")
    
    cities_df = run_query(f"SELECT DISTINCT [{food_loc}] FROM food_listings_data WHERE [{food_loc}] IS NOT NULL")
    food_types_df = run_query(f"SELECT DISTINCT [{food_type}] FROM food_listings_data WHERE [{food_type}] IS NOT NULL")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_city = st.selectbox("Filter by City Location:", ["All Cities"] + list(cities_df.iloc[:, 0].values if not cities_df.empty else []))
    with col2:
        selected_type = st.selectbox("Filter by Food Type:", ["All Types"] + list(food_types_df.iloc[:, 0].values if not food_types_df.empty else []))
        
    base_query = "SELECT * FROM food_listings_data WHERE 1=1"
    params = []
    if selected_city != "All Cities":
        base_query += f" AND [{food_loc}] = ?"
        params.append(selected_city)
    if selected_type != "All Types":
        base_query += f" AND [{food_type}] = ?"
        params.append(selected_type)
        
    if not params:
        final_listings = run_query(base_query)
    else:
        with sqlite3.connect(DB_FILE) as conn:
            final_listings = pd.read_sql_query(base_query, conn, params=params)
    st.dataframe(final_listings, use_container_width=True)

# ====================================================================
# TAB 2: 15 BUSINESS SQL QUERIES
# ====================================================================
elif menu == "🔍 15 Business SQL Queries":
    st.header("📊 Analytical Business Insights & Trends")
    
    queries = {
        "Query 1: Number of providers and receivers in each city": f"""
            SELECT [{prov_city}] AS City, 'Provider' AS Entity_Type, COUNT(*) AS Total_Count FROM providers_data GROUP BY [{prov_city}]
            UNION ALL
            SELECT [{recv_city}] AS City, 'Receiver' AS Entity_Type, COUNT(*) AS Total_Count FROM receivers_data GROUP BY [{recv_city}];
        """,
        "Query 2: Which type of provider contributes the most food?": f"""
            SELECT p.[{prov_type}] AS Provider_Type, SUM(CAST(f.[{food_qty}] AS INTEGER)) AS Total_Food_Contributed
            FROM providers_data p
            JOIN food_listings_data f ON p.[{prov_id}] = f.[{food_prov_fk}]
            GROUP BY p.[{prov_type}];
        """,
        "Query 3: Most commonly listed food items": f"""
            SELECT [{food_item}] AS Food_Item, SUM(CAST([{food_qty}] AS INTEGER)) AS Total_Quantity
            FROM food_listings_data
            GROUP BY [{food_item}]
            ORDER BY Total_Quantity DESC;
        """,
        "Query 4: Status of claims (Accepted, Pending, Rejected)": f"""
            SELECT [{claim_status}] AS Claim_Status, COUNT(*) AS Total_Claims
            FROM claims_data
            GROUP BY [{claim_status}];
        """,
        "Query 5: Top 3 cities with the highest food provider activity": f"""
            SELECT [{prov_city}] AS City, COUNT(*) AS Active_Providers
            FROM providers_data
            GROUP BY [{prov_city}]
            ORDER BY Active_Providers DESC
            LIMIT 3;
        """,
        "Query 6: Total quantity of food available across the entire system": f"""
            SELECT SUM(CAST([{food_qty}] AS INTEGER)) AS Total_Global_Food_Quantity 
            FROM food_listings_data;
        """,
        "Query 7: Average quantity per food listing grouped by Meal Type (Veg/Non-Veg)": f"""
            SELECT [{food_meal}] AS Meal_Type, AVG(CAST([{food_qty}] AS INTEGER)) AS Avg_Quantity_Per_Listing
            FROM food_listings_data
            GROUP BY [{food_meal}];
        """,
        "Query 8: List food items with a decent quantity (greater than 10 units)": f"""
            SELECT [{food_item}] AS Food_Name, [{food_qty}] AS Quantity, [{food_loc}] AS Location
            FROM food_listings_data
            WHERE CAST([{food_qty}] AS INTEGER) > 10;
        """,
        "Query 9: Count of receivers based on their type (NGO, Shelter, Individual)": f"""
            SELECT [{recv_type}] AS Receiver_Type, COUNT(*) AS Total_Receivers
            FROM receivers_data
            GROUP BY [{recv_type}];
        """,
        "Query 10: Find providers in your cities (Broad match case-insensitive)": f"""
            SELECT [{prov_name}] AS Provider_Name, [{prov_type}] AS Provider_Type, [{prov_city}] AS City 
            FROM providers_data 
            WHERE LOWER([{prov_city}]) LIKE '%pune%' 
               OR LOWER([{prov_city}]) LIKE '%nagpur%'
               OR [{prov_city}] IS NOT NULL;
        """,
        "Query 11: Find providers that have never listed any food items yet (Left Join)": f"""
            SELECT p.[{prov_name}] AS Inactive_Provider, p.[{prov_city}] AS City
            FROM providers_data p
            LEFT JOIN food_listings_data f ON p.[{prov_id}] = f.[{food_prov_fk}]
            WHERE f.[{food_id}] IS NULL;
        """,
        "Query 12: List details of all claims that aren't blank": f"""
            SELECT cl.[{claim_id}] AS Claim_ID, f.[{food_item}] AS Claimed_Food, cl.[{claim_status}] AS Status
            FROM claims_data cl
            JOIN food_listings_data f ON cl.[{claim_food_fk}] = f.[{food_id}]
            WHERE cl.[{claim_status}] IS NOT NULL AND cl.[{claim_status}] != ''
            ORDER BY cl.[{claim_status}];
        """,
        "Query 13: Track which receiver has made the most total claims": f"""
            SELECT r.[{recv_name}] AS Receiver_Name, COUNT(cl.[{claim_id}]) AS Total_Claims_Made
            FROM receivers_data r
            JOIN claims_data cl ON r.[{recv_id}] = cl.[{claim_recv_fk}]
            GROUP BY r.[{recv_name}]
            ORDER BY Total_Claims_Made DESC;
        """,
        "Query 14: Find the specific location hubs where food is stored for 'Pending' claims": f"""
            SELECT f.[{food_item}] AS Food_Name, f.[{food_loc}] AS Storage_Location, cl.[{claim_status}] AS Claim_Status
            FROM food_listings_data f
            JOIN claims_data cl ON f.[{food_id}] = cl.[{claim_food_fk}]
            WHERE LOWER(cl.[{claim_status}]) LIKE '%pending%' OR cl.[{claim_status}] IS NOT NULL;
        """,
        "Query 15: Find the breakdown of food types involved in claims": f"""
            SELECT f.[{food_type}] AS Food_Type, COUNT(cl.[{claim_id}]) AS Total_Claims_Involved
            FROM food_listings_data f
            JOIN claims_data cl ON f.[{food_id}] = cl.[{claim_food_fk}]
            WHERE f.[{food_type}] IS NOT NULL AND f.[{food_type}] != ''
            GROUP BY f.[{food_type}];
        """
    }
    
    selected_query_name = st.selectbox("Choose a Question to Query:", list(queries.keys()))
    st.code(queries[selected_query_name], language="sql")
    
    if st.button("Execute SQL Engine Query"):
        res_data = run_query(queries[selected_query_name])
        st.success("Query executed successfully!")
        st.dataframe(res_data, use_container_width=True)
