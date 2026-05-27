import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.incidents import get_all_incidents, update_incident_status

st.set_page_config(page_title="Shrink Agent", page_icon="🔍", layout="wide")

st.title("🔍 Shrink Agent — Loss Prevention Dashboard")
st.markdown("AI-powered retail anomaly detection. All alerts require human review before any action is taken.")
st.divider()

incidents = get_all_incidents()

if not incidents:
    st.info("No incidents detected yet. Run the agent to scan for anomalies.")
else:
    st.markdown(f"### {len(incidents)} Incident(s) Detected")

    for inc in incidents:
        risk = inc.get("risk_tier", "UNKNOWN")
        color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk, "⚪")

        with st.expander(f"{color} {risk} RISK — {inc['store_id']} | Employee {inc['employee_id']} | Register {inc['register_id']} | {inc['window_start']}"):

            col1, col2, col3 = st.columns(3)
            col1.metric("Risk Score", f"{inc.get('score', 0)}/100")
            col2.metric("Voids", inc.get("void_count", 0))
            col3.metric("Amount", f"${inc.get('total_void_amount', 0)}")

            st.markdown("**🤖 Gemini Alert:**")
            st.info(inc.get("alert_text", "No alert generated"))

            st.markdown("**📡 Signals Detected:**")
            for signal in inc.get("signals", []):
                st.markdown(f"- {signal}")

            st.markdown("**📦 Items Involved:**")
            st.markdown(", ".join(inc.get("items_involved", [])))

            st.markdown("**Current Status:**")
            status = inc.get("status", "OPEN")
            if status == "OPEN":
                col_a, col_b, col_c = st.columns(3)
                if col_a.button("✅ Confirm Theft", key=f"confirm_{inc['_id']}"):
                    update_incident_status(inc["_id"], "CONFIRMED_THEFT")
                    st.success("Marked as confirmed theft")
                    st.rerun()
                if col_b.button("❌ False Alarm", key=f"false_{inc['_id']}"):
                    update_incident_status(inc["_id"], "FALSE_ALARM")
                    st.success("Marked as false alarm")
                    st.rerun()
            else:
                st.markdown(f"**Reviewed:** `{status}`")