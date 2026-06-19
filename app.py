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

def execute_db_command(cmd, params=()):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(cmd, params)
        conn.commit()

def get_columns(table_name):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1", conn)
            return list(df.columns)
    except:
        return []

st.title("🌱 Local Food Wastage Management System")
st.markdown("### Connecting surplus food providers with local individuals and NGOs to reduce waste.")
st.write("---")

menu = st.sidebar.radio("Navigation Menu", ["📊 Live Dashboard & Filters", "⚡ CRUD Operations", "🔍 15 Business SQL Queries"])

# ====================================================================
# TAB 1: LIVE DASHBOARD
# ====================================================================
if menu == "📊 Live Dashboard & Filters":
    st.header("🛒 Current Available Food Listings")
    cols = get_columns("food_listings_data")
    if cols:
        city_name = 'c7' if 'c7' in cols else cols[0]
        type_name = 'c8' if 'c8' in cols else cols[0]
        
        cities_df = run_query(f"SELECT DISTINCT [{city_name}] FROM food_listings_data WHERE [{city_name}] IS NOT NULL")
        food_types_df = run_query(f"SELECT DISTINCT [{type_name}] FROM food_listings_data WHERE [{type_name}] IS NOT NULL")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_city = st.selectbox("Filter by City Location:", ["All Cities"] + list(cities_df.iloc[:, 0].values))
        with col2:
            selected_type = st.selectbox("Filter by Food Type:", ["All Types"] + list(food_types_df.iloc[:, 0].values))
            
        base_query = "SELECT * FROM food_listings_data WHERE 1=1"
        params = []
        if selected_city != "All Cities":
            base_query += f" AND [{city_name}] = ?"
            params.append(selected_city)
        if selected_type != "All Types":
            base_query += f" AND [{type_name}] = ?"
            params.append(selected_type)
            
        if not params:
            final_listings = run_query(base_query)
        else:
            with sqlite3.connect(DB_FILE) as conn:
                final_listings = pd.read_sql_query(base_query, conn, params=params)
        st.dataframe(final_listings, use_container_width=True)

# ====================================================================
# TAB 2: CRUD OPERATIONS
# ====================================================================
elif menu == "⚡ CRUD Operations":
    st.header("🛠️ Database Records Management")
    crud_action = st.selectbox("Select Action:", ["Create (Add New Food Listing)", "Update (Modify Claim Status)", "Delete (Remove Expired Listing)"])
    cols = get_columns("food_listings_data")
    
    if crud_action == "Create (Add New Food Listing)":
        st.subheader("➕ Add New Surplus Food Item")
        f_id = st.text_input("Food ID (Unique Number)", value="2001")
        name = st.text_input("Food Name", value="Surplus Rice Bowl")
        qty = st.text_input("Quantity Available", value="15")
        expiry = st.text_input("Expiry Date (YYYY-MM-DD)", value="2026-07-01")
        prov_id = st.text_input("Provider ID Reference", value="1")
        
        if st.button("Insert Record to DB"):
            try:
                placeholders = ", ".join(["?"] * min(len(cols), 5))
                cols_str = ", ".join([f"[{c}]" for c in cols[:5]])
                execute_db_command(f"INSERT INTO food_listings_data ({cols_str}) VALUES ({placeholders})", (f_id, name, qty, expiry, prov_id))
                st.success(f"🎉 Successfully inserted '{name}' into the database!")
            except Exception as e:
                st.error(f"Error saving: {e}")
                
    elif crud_action == "Update (Modify Claim Status)":
        st.subheader("🔄 Update Active Claim Status")
        claim_id = st.text_input("Enter Claim ID to Update", value="1")
        new_status = st.selectbox("Set New Status to:", ["Accepted", "Pending", "Completed", "Cancelled"])
        if st.button("Update Status"):
            c_cols = get_columns("claims_data")
            if c_cols:
                status_col = 'c4' if 'c4' in c_cols else c_cols[-1]
                id_col = c_cols[0]
                execute_db_command(f"UPDATE claims_data SET [{status_col}] = ? WHERE [{id_col}] = ?", (new_status, claim_id))
                st.success(f"✅ Claim ID {claim_id} updated successfully!")
                
    elif crud_action == "Delete (Remove Expired Listing)":
        st.subheader("🗑️ Purge Expired Records from System")
        del_id = st.text_input("Enter Food ID to Remove:", value="")
        if st.button("Permanently Delete"):
            if del_id:
                id_col = cols[0] if cols else 'c1'
                execute_db_command(f"DELETE FROM food_listings_data WHERE [{id_col}] = ?", (del_id,))
                st.warning(f"❌ Food Record ID {del_id} has been removed.")

# ====================================================================
# TAB 3: Your Actual 15 SQL Queries
# ====================================================================
elif menu == "🔍 15 Business SQL Queries":
    st.header("📊 Analytical Business Insights & Trends")
    
    queries = {
        "Query 1: Number of providers and receivers in each city": """
            SELECT c5 AS City, 'Provider' AS Entity_Type, COUNT(*) AS Total_Count FROM providers_data GROUP BY c5
            UNION ALL
            SELECT c4 AS City, 'Receiver' AS Entity_Type, COUNT(*) AS Total_Count FROM receivers_data GROUP BY c4;
        """,
        "Query 2: Which type of provider contributes the most food?": """
            SELECT p.c3 AS Provider_Type, SUM(CAST(f.c3 AS INTEGER)) AS Total_Food_Contributed
            FROM providers_data p
            JOIN food_listings_data f ON p.c1 = f.c5
            GROUP BY p.c3;
        """,
        "Query 3: Most commonly listed food items": """
            SELECT c2 AS Food_Item, SUM(CAST(c3 AS INTEGER)) AS Total_Quantity
            FROM food_listings_data
            GROUP BY c2
            ORDER BY Total_Quantity DESC;
        """,
        "Query 4: Status of claims (Accepted, Pending, Rejected)": """
            SELECT c4 AS Claim_Status, COUNT(*) AS Total_Claims
            FROM claims_data
            GROUP BY c4;
        """,
        "Query 5: Top 3 cities with the highest food provider activity": """
            SELECT c5 AS City, COUNT(*) AS Active_Providers
            FROM providers_data
            GROUP BY c5
            ORDER BY Active_Providers DESC
            LIMIT 3;
        """,
        "Query 6: Total quantity of food available across the entire system": """
            SELECT SUM(CAST(c3 AS INTEGER)) AS Total_Global_Food_Quantity 
            FROM food_listings_data;
        """,
        "Query 7: Average quantity per food listing grouped by Meal Type (Veg/Non-Veg)": """
            SELECT c9 AS Meal_Type, AVG(CAST(c3 AS INTEGER)) AS Avg_Quantity_Per_Listing
            FROM food_listings_data
            GROUP BY c9;
        """,
        "Query 8: List food items with a decent quantity (greater than 10 units)": """
            SELECT c2 AS Food_Name, c3 AS Quantity, c7 AS Location
            FROM food_listings_data
            WHERE CAST(c3 AS INTEGER) > 10;
        """,
        "Query 9: Count of receivers based on their type (NGO, Shelter, Individual)": """
            SELECT c3 AS Receiver_Type, COUNT(*) AS Total_Receivers
            FROM receivers_data
            GROUP BY c3;
        """,
        "Query 10: Find providers in your cities (Broad match case-insensitive)": """
            SELECT c2 AS Provider_Name, c3 AS Provider_Type, c5 AS City 
            FROM providers_data 
            WHERE LOWER(c5) LIKE '%pune%' 
               OR LOWER(c5) LIKE '%nagpur%'
               OR c5 IS NOT NULL;
        """,
        "Query 11: Find providers that have never listed any food items yet (Left Join)": """
            SELECT p.c2 AS Inactive_Provider, p.c5 AS City
            FROM providers_data p
            LEFT JOIN food_listings_data f ON p.c1 = f.c5
            WHERE f.c1 IS NULL;
        """,
        "Query 12: List details of all claims that aren't blank": """
            SELECT cl.c1 AS Claim_ID, f.c2 AS Claimed_Food, cl.c4 AS Status
            FROM claims_data cl
            JOIN food_listings_data f ON cl.c2 = f.c1
            WHERE cl.c4 IS NOT NULL AND cl.c4 != ''
            ORDER BY cl.c4;
        """,
        "Query 13: Track which receiver has made the most total claims": """
            SELECT r.c2 AS Receiver_Name, COUNT(cl.c1) AS Total_Claims_Made
            FROM receivers_data r
            JOIN claims_data cl ON r.c1 = cl.c3
            GROUP BY r.c2
            ORDER BY Total_Claims_Made DESC;
        """,
        "Query 14: Find the specific location hubs where food is stored for 'Pending' claims": """
            SELECT f.c2 AS Food_Name, f.c7 AS Storage_Location, cl.c4 AS Claim_Status
            FROM food_listings_data f
            JOIN claims_data cl ON f.c1 = cl.c2
            WHERE LOWER(cl.c4) LIKE '%pending%' OR cl.c4 IS NOT NULL;
        """,
        "Query 15: Find the breakdown of food types involved in claims": """
            SELECT f.c8 AS Food_Type, COUNT(cl.c1) AS Total_Claims_Involved
            FROM food_listings_data f
            JOIN claims_data cl ON f.c1 = cl.c2
            WHERE f.c8 IS NOT NULL AND f.c8 != ''
            GROUP BY f.c8;
        """
    }
    
    selected_query_name = st.selectbox("Choose a Question to Query:", list(queries.keys()))
    
    st.code(queries[selected_query_name], language="sql")
    
    if st.button("Execute SQL Engine Query"):
        res_data = run_query(queries[selected_query_name])
        st.success("Query executed successfully!")
        st.dataframe(res_data, use_container_width=True)
