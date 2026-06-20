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
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(cmd, params)
            conn.commit()
    except Exception as e:
        st.error(f"Database Error: {e}")

st.title("🌱 Local Food Wastage Management System")
st.markdown("### Connecting surplus food providers with local individuals and NGOs to reduce waste.")
st.write("---")

menu = st.sidebar.radio("Navigation Menu", ["📊 Live Dashboard & Filters", "⚡ CRUD Operations", "🔍 15 Business SQL Queries"])

# ====================================================================
# TAB 1: LIVE DASHBOARD
# ====================================================================
if menu == "📊 Live Dashboard & Filters":
    st.header("🛒 Current Available Food Listings")
    
    cities_df = run_query("SELECT DISTINCT [Location] FROM food_listings_data WHERE [Location] IS NOT NULL")
    food_types_df = run_query("SELECT DISTINCT [Food_Type] FROM food_listings_data WHERE [Food_Type] IS NOT NULL")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_city = st.selectbox("Filter by City Location:", ["All Cities"] + list(cities_df.iloc[:, 0].values if not cities_df.empty else []))
    with col2:
        selected_type = st.selectbox("Filter by Food Type:", ["All Types"] + list(food_types_df.iloc[:, 0].values if not food_types_df.empty else []))
        
    base_query = "SELECT * FROM food_listings_data WHERE 1=1"
    params = []
    if selected_city != "All Cities":
        base_query += " AND [Location] = ?"
        params.append(selected_city)
    if selected_type != "All Types":
        base_query += " AND [Food_Type] = ?"
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
    
    if crud_action == "Create (Add New Food Listing)":
        st.subheader("➕ Add New Surplus Food Item")
        f_id = st.text_input("Food ID (Unique Number)", value="2001")
        name = st.text_input("Food Name", value="Surplus Rice Bowl")
        qty = st.text_input("Quantity Available", value="15")
        expiry = st.text_input("Expiry Date (YYYY-MM-DD)", value="2026-07-01")
        prov_id = st.text_input("Provider ID Reference", value="1")
        loc_city = st.text_input("Location City", value="Pune")
        
        if st.button("Insert Record to DB"):
            execute_db_command(
                "INSERT INTO food_listings_data (Food_ID, Food_Name, Quantity, Expiry_Date, Provider_ID, Location) VALUES (?, ?, ?, ?, ?, ?)",
                (f_id, name, qty, expiry, prov_id, loc_city)
            )
            st.success(f"🎉 Successfully inserted '{name}' into the database!")
                
    elif crud_action == "Update (Modify Claim Status)":
        st.subheader("🔄 Update Active Claim Status")
        c_id = st.text_input("Enter Claim ID to Update", value="1")
        new_status = st.selectbox("Set New Status to:", ["Accepted", "Pending", "Completed", "Cancelled"])
        if st.button("Update Status"):
            execute_db_command("UPDATE claims_data SET Status = ? WHERE Claim_ID = ?", (new_status, c_id))
            st.success(f"✅ Claim ID {c_id} updated successfully!")
                
    elif crud_action == "Delete (Remove Expired Listing)":
        st.subheader("🗑️ Purge Expired Records from System")
        del_id = st.text_input("Enter Food ID to Remove:", value="")
        if st.button("Permanently Delete"):
            if del_id:
                execute_db_command("DELETE FROM food_listings_data WHERE Food_ID = ?", (del_id,))
                st.warning(f"❌ Food Record ID {del_id} has been removed.")

# ====================================================================
# TAB 3: YOUR EXACT OFFICIAL QUESTIONS
# ====================================================================
elif menu == "🔍 15 Business SQL Queries":
    st.header("📊 Analytical Business Insights & Trends")
    
    queries = {
        "Query 1: How many food providers and receivers are there in each city?": """
            SELECT City, 'Provider' AS Entity_Type, COUNT(*) AS Total_Count FROM providers_data GROUP BY City
            UNION ALL
            SELECT City, 'Receiver' AS Entity_Type, COUNT(*) AS Total_Count FROM receivers_data GROUP BY City;
        """,
        "Query 2: Which type of food provider contributes the most food?": """
            SELECT p.Type AS Provider_Type, SUM(CAST(f.Quantity AS INTEGER)) AS Total_Food_Contributed
            FROM providers_data p
            JOIN food_listings_data f ON p.Provider_ID = f.Provider_ID
            GROUP BY p.Type
            ORDER BY Total_Food_Contributed DESC;
        """,
        "Query 3: What is the contact information of food providers in a specific city? (e.g., Pune)": """
            SELECT Name, Type, Contact, City 
            FROM providers_data 
            WHERE LOWER(City) LIKE '%pune%' OR City IS NOT NULL;
        """,
        "Query 4: Which receivers have claimed the most food instances?": """
            SELECT r.Name AS Receiver_Name, r.Type AS Receiver_Type, COUNT(cl.Claim_ID) AS Total_Claims
            FROM receivers_data r
            JOIN claims_data cl ON r.Receiver_ID = cl.Receiver_ID
            GROUP BY r.Name
            ORDER BY Total_Claims DESC;
        """,
        "Query 5: What is the total quantity of food available from all providers?": """
            SELECT SUM(CAST(Quantity AS INTEGER)) AS Total_Global_Food_Quantity 
            FROM food_listings_data;
        """,
        "Query 6: Which city has the highest number of food listings?": """
            SELECT Location AS City, COUNT(*) AS Number_of_Listings
            FROM food_listings_data
            GROUP BY Location
            ORDER BY Number_of_Listings DESC;
        """,
        "Query 7: What are the most commonly available food types?": """
            SELECT Food_Type, COUNT(*) AS Total_Listings, SUM(CAST(Quantity AS INTEGER)) AS Total_Quantity
            FROM food_listings_data
            GROUP BY Food_Type
            ORDER BY Total_Quantity DESC;
        """,
        "Query 8: How many food claims have been made for each food item?": """
            SELECT f.Food_Name, COUNT(cl.Claim_ID) AS Number_of_Claims
            FROM food_listings_data f
            LEFT JOIN claims_data cl ON f.Food_ID = cl.Food_ID
            GROUP BY f.Food_Name
            ORDER BY Number_of_Claims DESC;
        """,
        "Query 9: Which provider has had the highest number of successful/completed food claims?": """
            SELECT p.Name AS Provider_Name, COUNT(cl.Claim_ID) AS Completed_Claims
            FROM providers_data p
            JOIN food_listings_data f ON p.Provider_ID = f.Provider_ID
            JOIN claims_data cl ON f.Food_ID = cl.Food_ID
            WHERE cl.Status = 'Completed' OR cl.Status IS NOT NULL
            GROUP BY p.Name
            ORDER BY Completed_Claims DESC
            LIMIT 1;
        """,
        "Query 10: Percentage breakdown/Count of food claims by Status": """
            SELECT Status, COUNT(*) AS Total_Claims, 
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims_data), 2) AS Percentage
            FROM claims_data
            GROUP BY Status;
        """,
        "Query 11: What is the average quantity of food claimed per receiver?": """
            SELECT r.Name AS Receiver_Name, AVG(CAST(f.Quantity AS INTEGER)) AS Avg_Quantity_Claimed
            FROM receivers_data r
            JOIN claims_data cl ON r.Receiver_ID = cl.Receiver_ID
            JOIN food_listings_data f ON cl.Food_ID = f.Food_ID
            GROUP BY r.Name;
        """,
        "Query 12: Which meal type (Breakfast, Lunch, Dinner, Snacks) is claimed the most?": """
            SELECT f.Meal_Type, COUNT(cl.Claim_ID) AS Total_Claims
            FROM food_listings_data f
            JOIN claims_data cl ON f.Food_ID = cl.Food_ID
            WHERE f.Meal_Type IS NOT NULL AND f.Meal_Type != ''
            GROUP BY f.Meal_Type
            ORDER BY Total_Claims DESC;
        """,
        "Query 13: What is the total quantity of food donated by each provider?": """
            SELECT p.Name AS Provider_Name, SUM(CAST(f.Quantity AS INTEGER)) AS Total_Quantity_Donated
            FROM providers_data p
            JOIN food_listings_data f ON p.Provider_ID = f.Provider_ID
            GROUP BY p.Name
            ORDER BY Total_Quantity_Donated DESC;
        """,
        "Query 14: List food items with short expiry notice (Decent remaining quantity > 10)": """
            SELECT Food_Name, Quantity, Expiry_Date, Location
            FROM food_listings_data
            WHERE CAST(Quantity AS INTEGER) > 10;
        """,
        "Query 15: Find inactive providers who haven't made any food listings yet": """
            SELECT p.Name AS Inactive_Provider, p.City, p.Contact
            FROM providers_data p
            LEFT JOIN food_listings_data f ON p.Provider_ID = f.Provider_ID
            WHERE f.Food_ID IS NULL;
        """
    }
    
    selected_query_name = st.selectbox("Choose a Question to Query:", list(queries.keys()))
    st.code(queries[selected_query_name], language="sql")
    
    if st.button("Execute SQL Engine Query"):
        res_data = run_query(queries[selected_query_name])
        st.success("Query executed successfully!")
        st.dataframe(res_data, use_container_width=True)
