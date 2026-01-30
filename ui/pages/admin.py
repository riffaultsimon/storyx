import streamlit as st
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from db.models import User, Story, Transaction
from db.session import SessionLocal
from db.settings import get_settings, update_settings
from credits.service import add_credits
from i18n import t


def show_admin_page():
    if not st.session_state.get("is_admin"):
        st.error(t("admin.denied"))
        return

    st.markdown(f"## {t('admin.header')}")

    db = SessionLocal()
    try:
        tab_overview, tab_users, tab_revenue, tab_costs, tab_models = st.tabs([
            t("admin.tab_overview"), t("admin.tab_users"), t("admin.tab_revenue"),
            t("admin.tab_costs"), t("admin.tab_models"),
        ])

        with tab_overview:
            _render_overview(db)
        with tab_users:
            _render_users(db)
        with tab_revenue:
            _render_revenue(db)
        with tab_costs:
            _render_costs(db)
        with tab_models:
            _render_models(db)
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
    col1.metric(t("admin.total_users"), total_users)
    col2.metric(t("admin.new_7d"), new_7d)
    col3.metric(t("admin.new_30d"), new_30d)
    col4.metric(t("admin.credits_circulation"), total_credits)

    total_stories = db.query(Story).count()
    status_counts = (
        db.query(Story.status, func.count(Story.id))
        .group_by(Story.status)
        .all()
    )
    status_map = dict(status_counts)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(t("admin.total_stories"), total_stories)
    col2.metric(t("admin.generating"), status_map.get("generating", 0))
    col3.metric(t("admin.processing"), status_map.get("tts_processing", 0))
    col4.metric(t("admin.ready"), status_map.get("ready", 0))
    col5.metric(t("admin.failed"), status_map.get("failed", 0))


def _render_users(db):
    search = st.text_input(t("admin.search_users"), placeholder=t("admin.search_placeholder"))

    query = db.query(User)
    if search:
        query = query.filter(
            User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )
    users = query.order_by(User.created_at.desc()).limit(100).all()

    if not users:
        st.info(t("admin.no_users"))
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
    st.markdown(f"#### {t('admin.grant_credits')}")
    with st.form("grant_credits"):
        grant_username = st.text_input(t("admin.username"))
        grant_amount = st.number_input(t("admin.credits_to_grant"), min_value=1, max_value=1000, value=5)
        grant_submitted = st.form_submit_button(t("admin.btn_grant"))

        if grant_submitted and grant_username:
            target = db.query(User).filter(User.username == grant_username).first()
            if target:
                add_credits(
                    db,
                    user_id=target.id,
                    credits=grant_amount,
                    description=f"Admin grant: {grant_amount} credits",
                )
                st.success(t("admin.granted", amount=grant_amount, username=grant_username))
                st.rerun()
            else:
                st.error(t("admin.user_not_found", username=grant_username))


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
    col1.metric(t("admin.total_revenue"), f"${total_revenue:.2f}")
    col2.metric(t("admin.revenue_7d"), f"${rev_7d:.2f}")
    col3.metric(t("admin.revenue_30d"), f"${rev_30d:.2f}")

    # Transaction history with type filter
    st.markdown(f"### {t('admin.txn_history')}")
    type_filter = st.selectbox(t("admin.type"), [t("admin.all"), t("admin.purchase"), t("admin.usage")])

    txn_query = db.query(Transaction).order_by(Transaction.created_at.desc())
    if type_filter == t("admin.purchase"):
        txn_query = txn_query.filter(Transaction.type == "purchase")
    elif type_filter == t("admin.usage"):
        txn_query = txn_query.filter(Transaction.type == "usage")
    transactions = txn_query.limit(200).all()

    if transactions:
        txn_data = []
        for txn in transactions:
            user = db.query(User).filter(User.id == txn.user_id).first()
            txn_data.append({
                "Date": txn.created_at.strftime("%Y-%m-%d %H:%M"),
                "User": user.username if user else txn.user_id[:8],
                "Type": txn.type,
                "Credits": txn.credits,
                "Amount": f"${txn.amount_usd:.2f}" if txn.amount_usd else "-",
                "Description": txn.description or "",
            })
        st.dataframe(txn_data, use_container_width=True)
    else:
        st.info(t("admin.no_txn"))

    # Revenue per week chart
    st.markdown(f"### {t('admin.revenue_week')}")
    weekly_purchases = (
        db.query(Transaction)
        .filter(Transaction.type == "purchase", Transaction.amount_usd > 0)
        .order_by(Transaction.created_at)
        .all()
    )
    if weekly_purchases:
        import pandas as pd

        df = pd.DataFrame([
            {"date": txn.created_at, "amount": txn.amount_usd or 0}
            for txn in weekly_purchases
        ])
        df["week"] = pd.to_datetime(df["date"]).dt.to_period("W").dt.start_time
        weekly = df.groupby("week")["amount"].sum().reset_index()
        weekly.columns = ["Week", "Revenue"]
        st.bar_chart(weekly.set_index("Week"))
    else:
        st.info(t("admin.no_revenue"))


def _render_costs(db):
    stories_with_costs = (
        db.query(Story)
        .filter(Story.cost_total is not None, Story.cost_total > 0)
        .all()
    )

    total_cost = sum(s.cost_total or 0 for s in stories_with_costs)
    avg_cost = total_cost / len(stories_with_costs) if stories_with_costs else 0

    total_revenue = (
        db.query(func.sum(Transaction.amount_usd))
        .filter(Transaction.type == "purchase")
        .scalar()
        or 0.0
    )
    margin = ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric(t("admin.total_api_cost"), f"${total_cost:.2f}")
    col2.metric(t("admin.avg_cost"), f"${avg_cost:.4f}")
    col3.metric(t("admin.profit_margin"), f"{margin:.1f}%")

    # Cost breakdown
    st.markdown(f"### {t('admin.cost_breakdown')}")
    total_gen = sum(s.cost_story_generation or 0 for s in stories_with_costs)
    total_cover = sum(s.cost_cover_image or 0 for s in stories_with_costs)
    total_tts = sum(s.cost_tts or 0 for s in stories_with_costs)
    total_bgm = sum(s.cost_bgm or 0 for s in stories_with_costs)

    breakdown_data = {
        "Component": [t("admin.comp_story_gen"), t("admin.comp_cover"), t("admin.comp_tts"), t("admin.comp_bgm")],
        "Total Cost": [f"${total_gen:.4f}", f"${total_cover:.4f}", f"${total_tts:.4f}", f"${total_bgm:.4f}"],
        "Stories": [len(stories_with_costs)] * 4,
    }
    st.dataframe(breakdown_data, use_container_width=True)

    # Per-story cost table
    st.markdown(f"### {t('admin.per_story_costs')}")
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
                "BGM Cost": f"${s.cost_bgm or 0:.4f}",
                "Total": f"${s.cost_total or 0:.4f}",
            })

        st.dataframe(cost_data, use_container_width=True)

        df = pd.DataFrame([
            {"date": s.created_at, "cost": s.cost_total or 0}
            for s in stories_with_costs
        ])
        if not df.empty:
            df = df.sort_values("date")
            df = df.set_index("date")
            st.line_chart(df["cost"])
    else:
        st.info(t("admin.no_cost_data"))


def _render_models(db):
    settings = get_settings(db)

    st.markdown(f"### {t('admin.model_config')}")
    st.caption(t("admin.model_config_note"))

    with st.form("model_settings"):
        st.markdown(f"#### {t('admin.story_gen')}")
        story_model = st.selectbox(
            t("admin.story_llm"),
            ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"],
            index=["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"].index(settings.story_model)
            if settings.story_model in ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"] else 0,
        )

        st.markdown(f"#### {t('admin.cover_image')}")
        image_providers = ["dalle3", "imagen3"]
        image_provider = st.selectbox(
            t("admin.image_provider"),
            image_providers,
            index=image_providers.index(settings.image_provider)
            if settings.image_provider in image_providers else 0,
            help=t("admin.image_help"),
        )

        st.markdown(f"#### {t('admin.tts')}")
        tts_models = ["gpt-4o-mini-tts", "tts-1", "tts-1-hd"]
        tts_model = st.selectbox(
            t("admin.tts_model"),
            tts_models,
            index=tts_models.index(settings.tts_model)
            if settings.tts_model in tts_models else 0,
        )

        st.markdown(f"#### {t('admin.bgm')}")
        bgm_enabled = st.toggle(
            t("admin.bgm_enable"),
            value=bool(settings.bgm_enabled),
        )
        bgm_providers = ["lyria2"]
        bgm_provider = st.selectbox(
            t("admin.bgm_provider"),
            bgm_providers,
            index=0,
            help=t("admin.bgm_help"),
            disabled=not bgm_enabled,
        )

        submitted = st.form_submit_button(t("admin.btn_save_config"))

        if submitted:
            update_settings(
                db,
                story_model=story_model,
                image_provider=image_provider,
                tts_model=tts_model,
                bgm_enabled=bgm_enabled,
                bgm_provider=bgm_provider if bgm_enabled else "none",
            )
            st.success(t("admin.config_saved"))
            st.rerun()

    # Current config summary
    st.markdown(f"### {t('admin.current_config')}")
    st.markdown(t("admin.cfg_story_model", model=settings.story_model))
    st.markdown(t("admin.cfg_image", provider=settings.image_provider))
    st.markdown(t("admin.cfg_tts", model=settings.tts_model))

    bgm_status = (
        t("admin.cfg_bgm_enabled", provider=settings.bgm_provider)
        if settings.bgm_enabled
        else t("admin.cfg_bgm_disabled")
    )
    st.markdown(t("admin.cfg_bgm", status=bgm_status))

    # API key status
    st.markdown(f"### {t('admin.api_key_status')}")
    from config import OPENAI_API_KEY, GOOGLE_SERVICE_ACCOUNT_FILE
    col1, col2 = st.columns(2)
    col1.markdown(t("admin.openai_status", status=t("admin.configured") if OPENAI_API_KEY else t("admin.missing")))
    col2.markdown(t("admin.google_status", status=t("admin.configured") if GOOGLE_SERVICE_ACCOUNT_FILE else t("admin.missing")))
