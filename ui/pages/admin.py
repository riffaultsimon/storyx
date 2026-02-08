import streamlit as st
from datetime import datetime, timedelta, timezone

import pandas as pd
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


# ── Overview ──────────────────────────────────────────────

def _render_overview(db):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # --- KPI row ---
    total_users = db.query(User).count()
    new_7d = db.query(User).filter(User.created_at >= week_ago).count()
    total_stories = db.query(Story).count()
    stories_today = db.query(Story).filter(Story.created_at >= today_start).count()
    total_credits = db.query(func.sum(User.credit_balance)).scalar() or 0
    total_revenue = (
        db.query(func.sum(Transaction.amount_usd))
        .filter(Transaction.type == "purchase")
        .scalar() or 0.0
    )

    # Active users = users who created a story in the last 7 days
    active_7d = (
        db.query(func.count(func.distinct(Story.user_id)))
        .filter(Story.created_at >= week_ago)
        .scalar() or 0
    )

    # Conversion = users with at least 1 story / total users
    users_with_stories = db.query(func.count(func.distinct(Story.user_id))).scalar() or 0
    conversion = (users_with_stories / total_users * 100) if total_users > 0 else 0
    avg_stories = total_stories / total_users if total_users > 0 else 0

    with st.container(border=True):
        st.markdown(f"#### {t('admin.kpi_title')}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("admin.total_users"), total_users, f"+{new_7d} (7d)")
        c2.metric(t("admin.total_stories"), total_stories, f"+{stories_today} {t('admin.stories_today').lower()}")
        c3.metric(t("admin.credits_circulation"), total_credits)
        c4.metric(t("admin.total_revenue"), f"€{total_revenue:.2f}")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric(t("admin.active_users_7d"), active_7d)
        c6.metric(t("admin.conversion_rate"), f"{conversion:.0f}%")
        c7.metric(t("admin.avg_stories_user"), f"{avg_stories:.1f}")
        c8.metric(t("admin.stories_today"), stories_today)

    # --- Story status breakdown ---
    status_counts = dict(
        db.query(Story.status, func.count(Story.id))
        .group_by(Story.status)
        .all()
    )

    with st.container(border=True):
        st.markdown(f"#### {t('admin.stories_section')}")
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric(t("admin.generating"), status_counts.get("generating", 0))
        sc2.metric(t("admin.processing"), status_counts.get("tts_processing", 0))
        sc3.metric(t("admin.ready"), status_counts.get("ready", 0))
        sc4.metric(t("admin.failed"), status_counts.get("failed", 0))

    # --- Growth charts ---
    col_left, col_right = st.columns(2)

    with col_left:
        with st.container(border=True):
            st.markdown(f"#### {t('admin.user_growth')}")
            signups = (
                db.query(User.created_at)
                .filter(User.created_at >= month_ago)
                .all()
            )
            if signups:
                df = pd.DataFrame(signups, columns=["date"])
                df["date"] = pd.to_datetime(df["date"]).dt.date
                daily = df.groupby("date").size().reset_index(name="signups")
                daily = daily.set_index("date")
                st.area_chart(daily, color="#FF8C00")
            else:
                st.caption(t("admin.no_chart_data"))

    with col_right:
        with st.container(border=True):
            st.markdown(f"#### {t('admin.story_trend')}")
            stories_30d = (
                db.query(Story.created_at)
                .filter(Story.created_at >= month_ago)
                .all()
            )
            if stories_30d:
                df = pd.DataFrame(stories_30d, columns=["date"])
                df["date"] = pd.to_datetime(df["date"]).dt.date
                daily = df.groupby("date").size().reset_index(name="stories")
                daily = daily.set_index("date")
                st.area_chart(daily, color="#FF6B6B")
            else:
                st.caption(t("admin.no_chart_data"))

    # --- Content distribution ---
    col_lang, col_mood = st.columns(2)

    with col_lang:
        with st.container(border=True):
            st.markdown(f"#### {t('admin.lang_distribution')}")
            lang_counts = dict(
                db.query(Story.language, func.count(Story.id))
                .group_by(Story.language)
                .all()
            )
            if lang_counts:
                df = pd.DataFrame(
                    list(lang_counts.items()), columns=["Language", "Count"]
                ).set_index("Language")
                st.bar_chart(df, color="#FFD93D")
            else:
                st.caption(t("admin.no_chart_data"))

    with col_mood:
        with st.container(border=True):
            st.markdown(f"#### {t('admin.mood_distribution')}")
            mood_counts = dict(
                db.query(Story.mood, func.count(Story.id))
                .filter(Story.mood.isnot(None))
                .group_by(Story.mood)
                .all()
            )
            if mood_counts:
                df = pd.DataFrame(
                    list(mood_counts.items()), columns=["Mood", "Count"]
                ).set_index("Mood")
                st.bar_chart(df, color="#74B9FF")
            else:
                st.caption(t("admin.no_chart_data"))

    # --- Top creators ---
    with st.container(border=True):
        st.markdown(f"#### {t('admin.top_creators')}")
        top = (
            db.query(User.username, func.count(Story.id).label("count"))
            .join(Story, Story.user_id == User.id)
            .group_by(User.username)
            .order_by(func.count(Story.id).desc())
            .limit(10)
            .all()
        )
        if top:
            df = pd.DataFrame(top, columns=["User", "Stories"]).set_index("User")
            st.bar_chart(df, color="#00B894", horizontal=True)
        else:
            st.caption(t("admin.no_chart_data"))


# ── Users ─────────────────────────────────────────────────

def _render_users(db):
    with st.container(border=True):
        search = st.text_input(t("admin.search_users"), placeholder=t("admin.search_placeholder"))

        query = db.query(User)
        if search:
            query = query.filter(
                User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
            )
        users = query.order_by(User.created_at.desc()).limit(100).all()

        if not users:
            st.info(t("admin.no_users"))
        else:
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

    with st.container(border=True):
        st.markdown(f"#### {t('admin.grant_credits')}")
        with st.form("grant_credits"):
            gc1, gc2 = st.columns([2, 1])
            with gc1:
                grant_username = st.text_input(t("admin.username"))
            with gc2:
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


# ── Revenue ───────────────────────────────────────────────

def _render_revenue(db):
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    purchases = db.query(Transaction).filter(Transaction.type == "purchase")
    total_revenue = purchases.with_entities(func.sum(Transaction.amount_usd)).scalar() or 0.0
    rev_7d = (
        purchases.filter(Transaction.created_at >= week_ago)
        .with_entities(func.sum(Transaction.amount_usd))
        .scalar() or 0.0
    )
    rev_30d = (
        purchases.filter(Transaction.created_at >= month_ago)
        .with_entities(func.sum(Transaction.amount_usd))
        .scalar() or 0.0
    )
    total_cost = db.query(func.sum(Story.cost_total)).scalar() or 0.0
    net_profit = total_revenue - total_cost

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("admin.total_revenue"), f"€{total_revenue:.2f}")
        c2.metric(t("admin.revenue_7d"), f"€{rev_7d:.2f}")
        c3.metric(t("admin.revenue_30d"), f"€{rev_30d:.2f}")
        c4.metric(
            t("admin.net_profit"),
            f"€{net_profit:.2f}",
            delta=f"€{net_profit:.2f}",
            delta_color="normal",
        )

    # Weekly revenue chart
    with st.container(border=True):
        st.markdown(f"#### {t('admin.revenue_week')}")
        weekly_purchases = (
            db.query(Transaction)
            .filter(Transaction.type == "purchase", Transaction.amount_usd > 0)
            .order_by(Transaction.created_at)
            .all()
        )
        if weekly_purchases:
            df = pd.DataFrame([
                {"date": txn.created_at, "amount": txn.amount_usd or 0}
                for txn in weekly_purchases
            ])
            df["week"] = pd.to_datetime(df["date"]).dt.to_period("W").dt.start_time
            weekly = df.groupby("week")["amount"].sum().reset_index()
            weekly.columns = ["Week", "Revenue"]
            st.bar_chart(weekly.set_index("Week"), color="#00B894")
        else:
            st.caption(t("admin.no_revenue"))

    # Transaction table
    with st.container(border=True):
        st.markdown(f"#### {t('admin.txn_history')}")
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
                    "Amount": f"€{txn.amount_usd:.2f}" if txn.amount_usd else "-",
                    "Description": txn.description or "",
                })
            st.dataframe(txn_data, use_container_width=True)
        else:
            st.info(t("admin.no_txn"))


# ── Costs ─────────────────────────────────────────────────

def _render_costs(db):
    stories_with_costs = (
        db.query(Story)
        .filter(Story.cost_total.isnot(None), Story.cost_total > 0)
        .all()
    )

    total_cost = sum(s.cost_total or 0 for s in stories_with_costs)
    avg_cost = total_cost / len(stories_with_costs) if stories_with_costs else 0
    total_revenue = (
        db.query(func.sum(Transaction.amount_usd))
        .filter(Transaction.type == "purchase")
        .scalar() or 0.0
    )
    margin = ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0

    # KPIs
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("admin.total_api_cost"), f"${total_cost:.2f}")
        c2.metric(t("admin.avg_cost"), f"${avg_cost:.4f}")
        c3.metric(t("admin.profit_margin"), f"{margin:.1f}%")
        c4.metric(t("admin.revenue_vs_cost"), f"${total_revenue - total_cost:.2f}")

    # Cost breakdown chart
    total_gen = sum(s.cost_story_generation or 0 for s in stories_with_costs)
    total_cover = sum(s.cost_cover_image or 0 for s in stories_with_costs)
    total_tts = sum(s.cost_tts or 0 for s in stories_with_costs)
    total_bgm = sum(s.cost_bgm or 0 for s in stories_with_costs)

    col_chart, col_table = st.columns(2)

    with col_chart:
        with st.container(border=True):
            st.markdown(f"#### {t('admin.cost_breakdown')}")
            breakdown = pd.DataFrame({
                "Component": [
                    t("admin.comp_story_gen"), t("admin.comp_cover"),
                    t("admin.comp_tts"), t("admin.comp_bgm"),
                ],
                "Cost": [total_gen, total_cover, total_tts, total_bgm],
            }).set_index("Component")
            if breakdown["Cost"].sum() > 0:
                st.bar_chart(breakdown, color="#FF8C00")
            else:
                st.caption(t("admin.no_cost_data"))

    with col_table:
        with st.container(border=True):
            st.markdown(f"#### {t('admin.cost_breakdown')}")
            st.dataframe({
                "Component": [
                    t("admin.comp_story_gen"), t("admin.comp_cover"),
                    t("admin.comp_tts"), t("admin.comp_bgm"),
                ],
                "Total": [f"${total_gen:.4f}", f"${total_cover:.4f}", f"${total_tts:.4f}", f"${total_bgm:.4f}"],
                "Avg/Story": [
                    f"${v:.4f}" for v in [
                        total_gen / max(len(stories_with_costs), 1),
                        total_cover / max(len(stories_with_costs), 1),
                        total_tts / max(len(stories_with_costs), 1),
                        total_bgm / max(len(stories_with_costs), 1),
                    ]
                ],
            }, use_container_width=True)

    # Cost trend over time
    with st.container(border=True):
        st.markdown(f"#### {t('admin.cost_trend')}")
        if stories_with_costs:
            cost_df = pd.DataFrame([
                {"date": s.created_at, "cost": s.cost_total or 0}
                for s in stories_with_costs if s.created_at
            ])
            if not cost_df.empty:
                cost_df = cost_df.sort_values("date").set_index("date")
                st.line_chart(cost_df["cost"], color="#FF6B6B")
        else:
            st.caption(t("admin.no_cost_data"))

    # Per-story cost table
    with st.container(border=True):
        st.markdown(f"#### {t('admin.per_story_costs')}")
        if stories_with_costs:
            cost_data = []
            for s in sorted(stories_with_costs, key=lambda x: x.created_at or datetime.min, reverse=True)[:50]:
                user = db.query(User).filter(User.id == s.user_id).first()
                cost_data.append({
                    "Title": s.title[:40],
                    "User": user.username if user else s.user_id[:8],
                    "Segments": s.segment_count or 0,
                    "TTS Chars": s.total_tts_chars or 0,
                    "Gen": f"${s.cost_story_generation or 0:.4f}",
                    "Cover": f"${s.cost_cover_image or 0:.4f}",
                    "TTS": f"${s.cost_tts or 0:.4f}",
                    "BGM": f"${s.cost_bgm or 0:.4f}",
                    "Total": f"${s.cost_total or 0:.4f}",
                })
            st.dataframe(cost_data, use_container_width=True)
        else:
            st.info(t("admin.no_cost_data"))


# ── Models ────────────────────────────────────────────────

def _render_models(db):
    settings = get_settings(db)

    # Current config summary
    with st.container(border=True):
        st.markdown(f"#### {t('admin.current_config')}")
        cfg1, cfg2 = st.columns(2)

        with cfg1:
            st.markdown(t("admin.cfg_story_model", model=settings.story_model))
            st.markdown(t("admin.cfg_image", provider=settings.image_provider))

        with cfg2:
            st.markdown(t("admin.cfg_tts", model=settings.tts_model))
            bgm_status = (
                t("admin.cfg_bgm_enabled", provider=settings.bgm_provider)
                if settings.bgm_enabled
                else t("admin.cfg_bgm_disabled")
            )
            st.markdown(t("admin.cfg_bgm", status=bgm_status))

    # API key status
    with st.container(border=True):
        st.markdown(f"#### {t('admin.api_key_status')}")
        from config import OPENAI_API_KEY, GOOGLE_SERVICE_ACCOUNT_FILE
        ak1, ak2 = st.columns(2)

        openai_ok = bool(OPENAI_API_KEY)
        google_ok = bool(GOOGLE_SERVICE_ACCOUNT_FILE)

        with ak1:
            st.markdown(
                f'{"&#9989;" if openai_ok else "&#10060;"} '
                + t("admin.openai_status", status=t("admin.configured") if openai_ok else t("admin.missing")),
                unsafe_allow_html=True,
            )
        with ak2:
            st.markdown(
                f'{"&#9989;" if google_ok else "&#10060;"} '
                + t("admin.google_status", status=t("admin.configured") if google_ok else t("admin.missing")),
                unsafe_allow_html=True,
            )

    # Configuration form
    with st.container(border=True):
        st.markdown(f"#### {t('admin.model_config')}")
        st.caption(t("admin.model_config_note"))

        with st.form("model_settings"):
            form1, form2 = st.columns(2)

            with form1:
                st.markdown(f"**{t('admin.story_gen')}**")
                story_model = st.selectbox(
                    t("admin.story_llm"),
                    ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"],
                    index=["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"].index(settings.story_model)
                    if settings.story_model in ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"] else 0,
                )

                st.markdown(f"**{t('admin.cover_image')}**")
                image_providers = ["dalle3", "imagen3"]
                image_provider = st.selectbox(
                    t("admin.image_provider"),
                    image_providers,
                    index=image_providers.index(settings.image_provider)
                    if settings.image_provider in image_providers else 0,
                    help=t("admin.image_help"),
                )

            with form2:
                st.markdown(f"**{t('admin.tts')}**")
                tts_models = ["gpt-4o-mini-tts", "tts-1", "tts-1-hd"]
                tts_model = st.selectbox(
                    t("admin.tts_model"),
                    tts_models,
                    index=tts_models.index(settings.tts_model)
                    if settings.tts_model in tts_models else 0,
                )

                st.markdown(f"**{t('admin.bgm')}**")
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
