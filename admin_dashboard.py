import streamlit as st
import pandas as pd
import mysql.connector
from config import DB_CONFIG
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="FaceSched HR Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Professional Look ---
st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        border: 1px solid #e0e0e0;
    }
    [data-testid="stMetricValue"] {
        color: #1f77b4;
        font-size: 1.8rem;
        font-weight: 600;
    }
    [data-testid="stMetricLabel"] {
        color: #333333;
        font-weight: 500;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
    h1 {
        color: #1f77b4;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# --- Database Connection Functions ---
@st.cache_data(ttl=300)
def get_data(start_date, end_date):
    """Fetches attendance logs for a date range."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        
        query = f"""
            SELECT 
                e.emp_id,
                e.name AS Name, 
                e.department AS Department,
                a.date AS Date,
                a.check_in AS Check_In, 
                a.check_out AS Check_Out, 
                a.status AS Status, 
                a.total_hours AS Hours
            FROM attendance a
            JOIN employees e ON a.emp_id = e.emp_id
            WHERE a.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY a.date DESC, a.check_in DESC
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Data cleaning
        if not df.empty:
            df['Check_In'] = pd.to_datetime(df['Check_In'], errors='coerce')
            df['Check_Out'] = pd.to_datetime(df['Check_Out'], errors='coerce')
            df['Date'] = pd.to_datetime(df['Date'])
            df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_employee_count():
    """Gets total registered employees."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

# --- Sidebar: Filters & Controls ---
st.sidebar.title("Control Panel")

# Date Range Selector
date_mode = st.sidebar.radio("View Mode", ["Today", "Date Range", "Last 7 Days", "Last 30 Days"])

if date_mode == "Today":
    start_date = end_date = date.today()
elif date_mode == "Last 7 Days":
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
elif date_mode == "Last 30 Days":
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
else:  # Date Range
    col1, col2 = st.sidebar.columns(2)
    start_date = col1.date_input("From", date.today() - timedelta(days=7))
    end_date = col2.date_input("To", date.today())

# Department Filter
df_full = get_data(start_date, end_date)
departments = ["All"] + sorted(df_full['Department'].unique().tolist()) if not df_full.empty else ["All"]
selected_dept = st.sidebar.selectbox("Department", departments)

# Apply department filter
if selected_dept != "All" and not df_full.empty:
    df = df_full[df_full['Department'] == selected_dept].copy()
else:
    df = df_full.copy()

if st.sidebar.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(f"Period: {start_date} to {end_date}\n\nDepartment: {selected_dept}")

# --- Main Dashboard ---
st.title("FaceSched HR Analytics Dashboard")
st.markdown("*Enterprise-level workforce insights and attendance analytics*")

# --- Key Performance Indicators ---
if not df.empty:
    total_employees = get_employee_count()
    unique_present = df['emp_id'].nunique()
    total_records = len(df)
    total_late = len(df[df['Status'] == 'late'])
    total_ontime = len(df[df['Status'] == 'present'])
    avg_hours = df['Hours'].mean() if df['Hours'].notna().any() else 0
    
    # Calculate attendance rate
    days_in_range = (end_date - start_date).days + 1
    expected_records = total_employees * days_in_range
    attendance_rate = (total_records / expected_records * 100) if expected_records > 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Records", total_records, f"{unique_present} unique employees")
    col2.metric("Attendance Rate", f"{attendance_rate:.1f}%", f"of {total_employees} employees")
    col3.metric("On Time", total_ontime, f"{(total_ontime/total_records*100):.1f}%" if total_records > 0 else "0%")
    col4.metric("Late Arrivals", total_late, f"{(total_late/total_records*100):.1f}%" if total_records > 0 else "0%")
    col5.metric("Avg Work Hours", f"{avg_hours:.1f}h", "per day")
    
    st.markdown("---")
    
    # --- Analytics Section ---
    tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Departments", "Employees", "Raw Data"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Daily Attendance Trend")
            daily_counts = df.groupby('Date').size().reset_index(name='Count')
            fig = px.line(daily_counts, x='Date', y='Count', markers=True,
                         title="Attendance Over Time")
            fig.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Status Distribution")
            status_counts = df['Status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index,
                        title="Present vs Late", 
                        color_discrete_sequence=['#00cc96', '#ff6b6b'])
            st.plotly_chart(fig, use_container_width=True)
        
        # Hourly Check-in Pattern
        st.subheader("Check-in Time Distribution")
        df['Check_In_Hour'] = df['Check_In'].dt.hour
        hourly_checkins = df['Check_In_Hour'].value_counts().sort_index()
        fig = px.bar(x=hourly_checkins.index, y=hourly_checkins.values,
                    labels={'x': 'Hour of Day', 'y': 'Number of Check-ins'},
                    title="Peak Check-in Hours")
        fig.update_traces(marker_color='#636efa')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Department-wise Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Department attendance
            dept_stats = df.groupby('Department').agg({
                'emp_id': 'count',
                'Status': lambda x: (x == 'present').sum(),
                'Hours': 'mean'
            }).reset_index()
            dept_stats.columns = ['Department', 'Total Records', 'On-Time', 'Avg Hours']
            dept_stats['Late'] = dept_stats['Total Records'] - dept_stats['On-Time']
            
            fig = px.bar(dept_stats, x='Department', y=['On-Time', 'Late'],
                        title="Punctuality by Department", barmode='stack',
                        color_discrete_map={'On-Time': '#00cc96', 'Late': '#ff6b6b'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(dept_stats, x='Department', y='Avg Hours',
                        title="Average Working Hours by Department")
            fig.update_traces(marker_color='#ab63fa')
            st.plotly_chart(fig, use_container_width=True)
        
        # Department details table
        st.dataframe(dept_stats, use_container_width=True, hide_index=True)
    
    with tab3:
        st.subheader("Employee Performance Insights")
        
        # Employee summary
        emp_summary = df.groupby(['emp_id', 'Name', 'Department']).agg({
            'Date': 'count',
            'Status': lambda x: (x == 'late').sum(),
            'Hours': 'mean'
        }).reset_index()
        emp_summary.columns = ['ID', 'Name', 'Department', 'Days Present', 'Late Count', 'Avg Hours']
        emp_summary['Punctuality %'] = ((emp_summary['Days Present'] - emp_summary['Late Count']) / 
                                        emp_summary['Days Present'] * 100).round(1)
        emp_summary = emp_summary.sort_values('Days Present', ascending=False)
        
        # Top performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Most Punctual Employees**")
            top_punctual = emp_summary.nlargest(5, 'Punctuality %')[['Name', 'Department', 'Punctuality %']]
            st.dataframe(top_punctual, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("**Needs Attention**")
            needs_attention = emp_summary.nsmallest(5, 'Punctuality %')[['Name', 'Department', 'Late Count']]
            st.dataframe(needs_attention, hide_index=True, use_container_width=True)
        
        # Full employee table with search
        st.markdown("**All Employee Statistics**")
        search = st.text_input("Search employee", "")
        if search:
            emp_summary = emp_summary[emp_summary['Name'].str.contains(search, case=False)]
        st.dataframe(emp_summary, use_container_width=True, hide_index=True)
    
    with tab4:
        st.subheader("Detailed Attendance Logs")
        
        # Format times for display
        df_display = df.copy()
        df_display['Check_In'] = df_display['Check_In'].dt.strftime('%H:%M:%S')
        df_display['Check_Out'] = df_display['Check_Out'].dt.strftime('%H:%M:%S')
        df_display['Date'] = df_display['Date'].dt.strftime('%Y-%m-%d')
        
        # Search and filter
        search_log = st.text_input("Search logs", "", key="log_search")
        if search_log:
            df_display = df_display[df_display['Name'].str.contains(search_log, case=False)]
        
        # Display options
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            if st.button("Download CSV"):
                csv = df_display.to_csv(index=False)
                st.download_button("Download", csv, "attendance_data.csv", "text/csv")
        
        # Display table
        st.dataframe(
            df_display[['Date', 'Name', 'Department', 'Check_In', 'Check_Out', 'Status', 'Hours']],
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning(f"No attendance records found for the selected period.")
    st.info("Try adjusting the date range or department filter.")

# --- Footer ---
st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.caption("FaceSched AI | HR Analytics Dashboard v2.0")
with col2:
    st.caption(f"Last Updated: {date.today()}")
with col3:
    if st.button("Help"):
        st.info("""
        **Dashboard Features:**
        - Real-time attendance tracking
        - Trend analysis & insights
        - Department comparisons
        - Employee performance metrics
        - Data export capabilities
        """)