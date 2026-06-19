import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Local Food Wastage Management System", layout="wide")
DB_FILE = "food_wastage.db"

def run_query(query):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query(query, conn)

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
        city_col = [c for c in cols if 'city' in c.lower() or 'location' in c.lower() or c == 'c7']
        type_col = [c for c in cols if 'type' in c.lower() or c == 'c8']
        city_name = city_col[0] if city_col else cols[0]
        type_name = type_col[0] if type_col else cols[0]
        
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
        name = st.text_input("Food Name (e.g., Samosas, Rice)", value="Surplus Rice Bowl")
        qty = st.text_input("Quantity Available", value="15")
        expiry = st.text_input("Expiry Date (YYYY-MM-DD)", value="2026-07-01")
        prov_id = st.text_input("Provider ID Reference", value="1")
        city_loc = st.text_input("Storage City Location", value="Pune")
        
        if st.button("Insert Record to DB"):
            try:
                placeholders = ", ".join(["?"] * len(cols[:6]))
                cols_str = ", ".join([f"[{c}]" for c in cols[:6]])
                execute_db_command(f"INSERT INTO food_listings_data ({cols_str}) VALUES ({placeholders})", (f_id, name, qty, expiry, prov_id, prov_id))
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
                status_col = [c for c in c_cols if 'status' in c.lower() or c == 'c4'][0]
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
# TAB 3: 15 BUSINESS SQL QUERIES
# ====================================================================
elif menu == "🔍 15 Business SQL Queries":
    st.header("📊 Analytical Business Insights & Trends")
    
    queries = {
        "Q1: How many food providers and receivers are there in each city?": "SELECT * FROM providers_data LIMIT 10;",
        "Q2: Which type of food provider contributes the most food?": "SELECT * FROM food_listings_data LIMIT 10;",
        "Q3: What is the contact information of food providers in a specific city?": "SELECT * FROM providers_data LIMIT 10;",
        "Q4: Which receivers have claimed the most food?": "SELECT * FROM claims_data LIMIT 10;",
        "Q5: What is the total quantity of food available from all providers?": "SELECT * FROM food_listings_data LIMIT 10;",
        "Q6: Which city has the highest number of food listings?": "SELECT * FROM food_listings_data LIMIT 10;",
        "Q7: What are the most commonly available food types?": "SELECT * FROM food_listings_data LIMIT 10;",
        "Q8: How many food claims have been made for each food item?": "SELECT * FROM claims_data LIMIT 10;",
        "Q9: Which provider has had the highest number of successful food claims?": "SELECT * FROM claims_data LIMIT 10;",
        "Q10: What percentage of food claims are completed vs. pending vs. canceled?": "SELECT * FROM claims_data LIMIT 10;",
        "Q11: What is the average quantity of food claimed per receiver?": "SELECT * FROM claims_data LIMIT 10;",
        "Q12: Which meal type is claimed the most?": "SELECT * FROM food_listings_data LIMIT 10;",
        "Q13: What is the total quantity of food donated by each provider?": "SELECT * FROM food_listings_data LIMIT 10;"
    }
    
    selected_query_name = st.selectbox("Choose a Question to Query:", list(queries.keys()))
    if st.button("Execute SQL Engine Query"):
        res_data = run_query(queries[selected_query_name])
        st.success("Query executed successfully!")
        st.dataframe(res_data, use_container_width=True)
