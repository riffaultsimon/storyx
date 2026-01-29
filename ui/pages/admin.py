import streamlit as st
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from db.models import User, Story, Transaction
from db.session import SessionLocal
from credits.service import add_credits


def show_admin_page():
    if not st.session_state.get("is_admin"):
        st.error("Access denied.")
        return

    st.markdown("## Admin Dashboard")

    db = SessionLocal()
    try:
        tab_overview, tab_users, tab_revenue, tab_costs = st.tabs(
            ["Overview", "Users", "Revenue", "API Costs"]
        )

        with tab_overview:
            _render_overview(db)

        with tab_users:
            _render_users(db)

        with tab_revenue:
            _render_revenue(db)

        with tab_costs:
            _render_costs(db)
    finally:
        db.close()


def _render_overview(db):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = db.query(User).count()
    new_7d = db.query(User).filter(User.created_at >= week_ago).count()
    new_30d = db.query(User).filter(User.created_at >= month_ago).count()
    total_credits = db.query(func.sum(User.credit_balance)).scalar() or 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Users", total_users)
    col2.metric("New (7d)", new_7d)
    col3.metric("New (30d)", new_30d)
    col4.metric("Credits in Circulation", total_credits)

    total_stories = db.query(Story).count()
    status_counts = (
        db.query(Story.status, func.count(Story.id))
        .group_by(Story.status)
        .all()
    )
    status_map = dict(status_counts)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Stories", total_stories)
    col2.metric("Generating", status_map.get("generating", 0))
    col3.metric("Processing", status_map.get("tts_processing", 0))
    col4.metric("Ready", status_map.get("ready", 0))
    col5.metric("Failed", status_map.get("failed", 0))


def _render_users(db):
    search = st.text_input("Search users", placeholder="Username or email")

    query = db.query(User)
    if search:
        query = query.filter(
            User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )
    users = query.order_by(User.created_at.desc()).limit(100).all()

    if not users:
        st.info("No users found.")
        return

    table_data = []
    for u in users:
        story_count = db.query(Story).filter(Story.user_id == u.id).count()
        table_data.append({
            "Username": u.username,
            "Email": u.email,
            "Joined": u.created_at.strftime("%Y-%m-%d"),
            "Stories": story_count,
            "Credits": u.credit_balance,
            "Admin": "Yes" if u.is_admin else "No",
        })

    st.dataframe(table_data, use_container_width=True)

    # Grant credits
    st.markdown("#### Grant Credits")
    with st.form("grant_credits"):
        grant_username = st.text_input("Username")
        grant_amount = st.number_input("Credits to grant", min_value=1, max_value=1000, value=5)
        grant_submitted = st.form_submit_button("Grant Credits")

        if grant_submitted and grant_username:
            target = db.query(User).filter(User.username == grant_username).first()
            if target:
                add_credits(
                    db,
                    user_id=target.id,
                    credits=grant_amount,
                    description=f"Admin grant: {grant_amount} credits",
                )
                st.success(f"Granted {grant_amount} credits to {grant_username}.")
                st.rerun()
            else:
                st.error(f"User '{grant_username}' not found.")


def _render_revenue(db):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    purchases = db.query(Transaction).filter(Transaction.type == "purchase")

    total_revenue = purchases.with_entities(func.sum(Transaction.amount_usd)).scalar() or 0.0
    rev_7d = (
        purchases.filter(Transaction.created_at >= week_ago)
        .with_entities(func.sum(Transaction.amount_usd))
        .scalar()
        or 0.0
    )
    rev_30d = (
        purchases.filter(Transaction.created_at >= month_ago)
        .with_entities(func.sum(Transaction.amount_usd))
        .scalar()
        or 0.0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_revenue:.2f}")
    col2.metric("Revenue (7d)", f"${rev_7d:.2f}")
    col3.metric("Revenue (30d)", f"${rev_30d:.2f}")

    # Transaction history with type filter
    st.markdown("### Transaction History")
    type_filter = st.selectbox("Type", ["All", "purchase", "usage"])

    txn_query = db.query(Transaction).order_by(Transaction.created_at.desc())
    if type_filter != "All":
        txn_query = txn_query.filter(Transaction.type == type_filter)
    transactions = txn_query.limit(200).all()

    if transactions:
        txn_data = []
        for t in transactions:
            user = db.query(User).filter(User.id == t.user_id).first()
            txn_data.append({
                "Date": t.created_at.strftime("%Y-%m-%d %H:%M"),
                "User": user.username if user else t.user_id[:8],
                "Type": t.type,
                "Credits": t.credits,
                "Amount": f"${t.amount_usd:.2f}" if t.amount_usd else "-",
                "Description": t.description or "",
            })
        st.dataframe(txn_data, use_container_width=True)
    else:
        st.info("No transactions found.")

    # Revenue per week chart
    st.markdown("### Revenue per Week")
    weekly_purchases = (
        db.query(Transaction)
        .filter(Transaction.type == "purchase", Transaction.amount_usd > 0)
        .order_by(Transaction.created_at)
        .all()
    )
    if weekly_purchases:
        import pandas as pd

        df = pd.DataFrame([
            {"date": t.created_at, "amount": t.amount_usd or 0}
            for t in weekly_purchases
        ])
        df["week"] = pd.to_datetime(df["date"]).dt.to_period("W").dt.start_time
        weekly = df.groupby("week")["amount"].sum().reset_index()
        weekly.columns = ["Week", "Revenue"]
        st.bar_chart(weekly.set_index("Week"))
    else:
        st.info("No revenue data yet.")


def _render_costs(db):
    stories_with_costs = (
        db.query(Story)
        .filter(Story.cost_total is not None, Story.cost_total > 0)
        .all()
    )

    total_cost = sum(s.cost_total or 0 for s in stories_with_costs)
    avg_cost = total_cost / len(stories_with_costs) if stories_with_costs else 0

    # Calculate total revenue for margin
    total_revenue = (
        db.query(func.sum(Transaction.amount_usd))
        .filter(Transaction.type == "purchase")
        .scalar()
        or 0.0
    )
    margin = ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total API Cost", f"${total_cost:.2f}")
    col2.metric("Avg Cost/Story", f"${avg_cost:.4f}")
    col3.metric("Profit Margin", f"{margin:.1f}%")

    # Cost breakdown
    st.markdown("### Cost Breakdown")
    total_gen = sum(s.cost_story_generation or 0 for s in stories_with_costs)
    total_cover = sum(s.cost_cover_image or 0 for s in stories_with_costs)
    total_tts = sum(s.cost_tts or 0 for s in stories_with_costs)

    breakdown_data = {
        "Component": ["Story Generation (GPT-4o)", "Cover Image (DALL-E 3)", "TTS"],
        "Total Cost": [f"${total_gen:.4f}", f"${total_cover:.4f}", f"${total_tts:.4f}"],
        "Stories": [len(stories_with_costs)] * 3,
    }
    st.dataframe(breakdown_data, use_container_width=True)

    # Per-story cost table
    st.markdown("### Per-Story Costs")
    if stories_with_costs:
        import pandas as pd

        cost_data = []
        for s in sorted(stories_with_costs, key=lambda x: x.created_at or datetime.min, reverse=True)[:50]:
            user = db.query(User).filter(User.id == s.user_id).first()
            cost_data.append({
                "Title": s.title[:40],
                "User": user.username if user else s.user_id[:8],
                "Segments": s.segment_count or 0,
                "TTS Chars": s.total_tts_chars or 0,
                "Gen Cost": f"${s.cost_story_generation or 0:.4f}",
                "Cover Cost": f"${s.cost_cover_image or 0:.4f}",
                "TTS Cost": f"${s.cost_tts or 0:.4f}",
                "Total": f"${s.cost_total or 0:.4f}",
            })

        st.dataframe(cost_data, use_container_width=True)

        # Cost chart
        df = pd.DataFrame([
            {
                "date": s.created_at,
                "cost": s.cost_total or 0,
            }
            for s in stories_with_costs
        ])
        if not df.empty:
            df = df.sort_values("date")
            df = df.set_index("date")
            st.line_chart(df["cost"])
    else:
        st.info("No cost data available yet.")
