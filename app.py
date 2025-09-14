import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Marketing Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Data Loading and Preparation ---
@st.cache_data
def load_and_prepare_data():
    # Load the datasets
    facebook_df = pd.read_csv('Facebook.csv')
    google_df = pd.read_csv('Google.csv')
    tiktok_df = pd.read_csv('TikTok.csv')
    business_df = pd.read_csv('business.csv')

    # Add a 'source' column
    facebook_df['source'] = 'Facebook'
    google_df['source'] = 'Google'
    tiktok_df['source'] = 'TikTok'

    # Combine marketing data
    marketing_df = pd.concat([facebook_df, google_df, tiktok_df], ignore_index=True)

    # Convert date columns to datetime
    marketing_df['date'] = pd.to_datetime(marketing_df['date'])
    business_df['date'] = pd.to_datetime(business_df['date'])

    # Aggregate marketing data by date
    marketing_agg_df = marketing_df.groupby('date').agg({
        'spend': 'sum',
        'impression': 'sum',
        'clicks': 'sum',
        'attributed revenue': 'sum'
    }).reset_index()

    # Merge with business data
    df = pd.merge(business_df, marketing_agg_df, on='date', how='left')
    
    # Rename columns
    df.rename(columns={
        '# of orders': 'orders',
        '# of new orders': 'new_orders',
        'new customers': 'new_customers',
        'total revenue': 'total_revenue',
        'gross profit': 'gross_profit',
        'attributed revenue': 'attributed_revenue'
    }, inplace=True)

    # Derived Metrics
    df['roas'] = df['attributed_revenue'] / df['spend']
    df['cpc'] = df['spend'] / df['clicks']
    df['ctr'] = df['clicks'] / df['impression']
    df['cpa'] = df['spend'] / df['new_customers']
    df['aov'] = df['total_revenue'] / df['orders']

    return df, marketing_df

df, marketing_df_raw = load_and_prepare_data()


# --- Dashboard UI ---
st.title("📈 Marketing Intelligence Dashboard")
st.markdown("Connecting marketing activities with business outcomes.")

# --- Date Filter ---
st.sidebar.header("Filters")
min_date = df['date'].min().to_pydatetime()
max_date = df['date'].max().to_pydatetime()

start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Filter data based on date range
mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
filtered_df = df.loc[mask]

# --- Key Metrics ---
st.header("Overall Performance")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${filtered_df['total_revenue'].sum():,.2f}")
col2.metric("Gross Profit", f"${filtered_df['gross_profit'].sum():,.2f}")
col3.metric("Total Spend", f"${filtered_df['spend'].sum():,.2f}")
col4.metric("ROAS", f"{filtered_df['attributed_revenue'].sum() / filtered_df['spend'].sum():.2f}x")

# --- Charts ---
st.header("Visualizations")

# Time Series Chart
st.subheader("Revenue, Spend, and ROAS Over Time")
fig_time_series = px.line(filtered_df, x='date', y=['total_revenue', 'spend'], title='Total Revenue and Marketing Spend')
fig_time_series.add_scatter(x=filtered_df['date'], y=filtered_df['roas'], yaxis="y2", name='ROAS', mode='lines')
fig_time_series.update_layout(yaxis2=dict(title='ROAS', overlaying='y', side='right'))
st.plotly_chart(fig_time_series, use_container_width=True)

# Marketing Channel Performance
st.subheader("Marketing Channel Performance")
channel_perf = marketing_df_raw.groupby('source').agg({
    'spend': 'sum',
    'attributed revenue': 'sum'
}).reset_index()
channel_perf['roas'] = channel_perf['attributed revenue'] / channel_perf['spend']

fig_channels = px.bar(channel_perf, x='source', y='attributed revenue', color='source', title='Attributed Revenue by Channel',
                        hover_data=['spend', 'roas'])
st.plotly_chart(fig_channels, use_container_width=True)

# --- Raw Data ---
st.header("Prepared Data")
st.dataframe(filtered_df)