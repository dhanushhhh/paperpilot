import streamlit as st
import time
from datetime import datetime
from newspaper_delivery_agent import create_distance_matrix, solve_vrp, delivery_points, locations, generate_delivery_summary


# --- App Config ---
st.set_page_config(page_title="PaperPilot - Newspaper Delivery", page_icon="🗞️")
st.markdown("<h1 style='text-align: center;'>🗞️ PaperPilot</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: grey;'>Starting your day, the PaperPilot way.</h4>", unsafe_allow_html=True)
st.markdown("---")


# --- Newspaper Setup ---
if "papers_to_collect" not in st.session_state:
    st.session_state.papers_to_collect = {
        "Malayalam (Malabar)": 1,
        "The New Indian Express": 1,
        "The South India Times": 1,
        "Kannada Prabha": 2,
        "Tamil (Daily Thanthi)": 2,
        "Salar (Urdu)": 3,
        "The Economic Times (ET)": 6,
        "Bangalore Mirror": 6,
        "Rajasthan Patrika (Hindi)": 6,
        "Deccan Herald": 9,
        "The Hindu": 14,
        "Prajavani (ಪ್ರಜಾವಾಣಿ)": 12,
        "Vijayavani (ವಿಜಯವಾಣಿ)": 12,
        "Vijaya Karnataka (VK)": 17,
        "Times of India (TOI)": 39
    }

papers_to_collect = st.session_state.papers_to_collect

# --- Initialize Session State ---
if "start_times" not in st.session_state:
    st.session_state.start_times = {}
if "completion_times" not in st.session_state:
    st.session_state.completion_times = {}
if "completed_deliveries" not in st.session_state:
    st.session_state.completed_deliveries = set()
if "route" not in st.session_state:
    distance_matrix = create_distance_matrix(locations)
    route = solve_vrp(distance_matrix)
    st.session_state.route = route
if "papers_collected" not in st.session_state:
    st.session_state.papers_collected = {}
if "total_paper_count" not in st.session_state:
    st.session_state.total_paper_count = None

route = st.session_state.route

# --- Newspaper Collection Section ---
st.markdown("### 📰 Today's Paper Stack:")

# --- Buttons ---
col1, col2, col3 = st.columns([1,1,2])
with col1:
    if st.button("📥 Mark All"):
        for paper in papers_to_collect:
            st.session_state.papers_collected[paper] = True
with col2:
    if st.button("🗑️ Clear All"):
        for paper in papers_to_collect:
            st.session_state.papers_collected[paper] = False
with col3:
    selected_paper = st.selectbox("✏️ Select Paper to Edit", ["-- Select a Paper --"] + list(papers_to_collect.keys()))

    if selected_paper != "-- Select a Paper --":
        new_count = st.number_input(
            f"Update count for {selected_paper}",
            min_value=0,
            value=st.session_state.papers_to_collect[selected_paper],
            step=1,
            key=f"edit_{selected_paper}"
        )
        st.session_state.papers_to_collect[selected_paper] = new_count



# Refresh after edit
papers_to_collect = st.session_state.papers_to_collect

# --- Newspaper Checkboxes with bold paper count ---
cols = st.columns(2)
left_items = list(papers_to_collect.items())[:len(papers_to_collect)//2 + 1]
right_items = list(papers_to_collect.items())[len(papers_to_collect)//2 + 1:]

with cols[0]:
    for paper, count in left_items:
        if paper not in st.session_state.papers_collected:
            st.session_state.papers_collected[paper] = False
        st.session_state.papers_collected[paper] = st.checkbox(
            f"**{count}×** {paper}", 
            value=st.session_state.papers_collected[paper], 
            key=f"left_{paper}"
        )

with cols[1]:
    for paper, count in right_items:
        if paper not in st.session_state.papers_collected:
            st.session_state.papers_collected[paper] = False
        st.session_state.papers_collected[paper] = st.checkbox(
            f"**{count}×** {paper}", 
            value=st.session_state.papers_collected[paper], 
            key=f"right_{paper}"
        )


# --- Papers Collection Status ---
if all(st.session_state.papers_collected.values()):
    st.success(f"✅ All newspapers collected on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.warning("📦 Please collect all newspapers before starting delivery.")

# --- Total Paper Count Button ---
if st.button("📦 Show Total Paper Count"):
    total_papers = sum(count for paper, count in papers_to_collect.items() if st.session_state.papers_collected.get(paper, False))
    st.session_state.total_paper_count = total_papers

# --- Display Total Paper Count ---
if st.session_state.total_paper_count is not None:
    st.info(f"🧮 Total Papers to Carry: **{st.session_state.total_paper_count}** papers (based on selected newspapers)")


# --- Timer State Initialization ---
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "total_elapsed" not in st.session_state:
    st.session_state.total_elapsed = 0
if "timer_paused" not in st.session_state:
    st.session_state.timer_paused = False
if "timer_finished" not in st.session_state:
    st.session_state.timer_finished = False

# --- Timer Buttons ---
st.markdown("### ⏱️ Delivery Timer Controls:")

col_timer1, col_timer2, col_timer3 = st.columns(3)

with col_timer1:
    if st.button("▶️ Start"):
        if not st.session_state.timer_running and not st.session_state.timer_paused:
            st.session_state.timer_start = time.time()
        elif st.session_state.timer_paused:
            st.session_state.timer_start = time.time()
            st.session_state.timer_paused = False
        st.session_state.timer_running = True
        st.session_state.timer_finished = False

with col_timer2:
    if st.session_state.timer_running:
        if st.button("⏸️ Pause"):
            elapsed = time.time() - st.session_state.timer_start
            st.session_state.total_elapsed += elapsed
            st.session_state.timer_running = False
            st.session_state.timer_paused = True
            st.rerun()  # Update UI immediately after pausing
    elif st.session_state.timer_paused:
        if st.button("▶️ Resume"):
            st.session_state.timer_start = time.time()
            st.session_state.timer_running = True
            st.session_state.timer_paused = False
            st.rerun()  # Update UI immediately after resuming


with col_timer3:
    if st.button("🏁 Finish"):
        if st.session_state.timer_running:
            elapsed = time.time() - st.session_state.timer_start
            st.session_state.total_elapsed += elapsed
        st.session_state.timer_running = False
        st.session_state.timer_finished = True
        st.session_state.timer_paused = False

# --- Timer Display ---
timer_placeholder = st.empty()

def format_time(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} seconds"
    else:
        minutes = seconds // 60
        sec = seconds % 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} {sec} seconds"

if st.session_state.timer_running:
    elapsed = time.time() - st.session_state.timer_start + st.session_state.total_elapsed
    timer_placeholder.info(f"⏳ Delivery Time Running: **{format_time(elapsed)}**")
    time.sleep(1)  # Wait for 1 second
    st.rerun()

elif st.session_state.timer_paused:
    timer_placeholder.warning(f"⏸️ Delivery Paused at: **{format_time(st.session_state.total_elapsed)}**")

elif st.session_state.timer_finished:
    timer_placeholder.success(f"🏁 Delivery Completed! Total Time: **{format_time(st.session_state.total_elapsed)}**")



# --- House-wise Papers List ---
house_papers_list = [
    "Hindu",
    "TOI, ET",
    "TOI",
    "TOI",
    "Prajavani",
    "TOI (2nd floor)", 
    "Vijayavani, Indian Express",
    "TOI",
    "Prajavani (Taranga)",
    "VK, TOI (Book)",
    "VK",
    "Vijayavani, Deccan",
    "TOI, Prajavani",
    "ET, Hindu",
    "Hindu, ET",
    "VK",
    "VK, Hindu",
    "Patrika",
    "TOI",
    "TOI, VK, Hindu",
    "South India times (new sri ram)",
    "VK",
    "ET, Mirror",
    "TOI",
    "Salar",
    "TOI, Vijayavani",
    "TOI, Vijayavani",
    "Deccan, Salar",
    "TOI (Church)",
    "TOI, TOI, Patrika, Patrika, Deccan, Patrika",
    "TOI",
    "Prajavani",
    "VK (Sun-Praja)",
    "VK",
    "Hindu, TOI",
    "Mirror, TOI",
    "TOI",
    "VK",
    "Deccan, Hindu, TOI",
    "TOI, VK (Sat - Bodhi)",
    "Patrika",
    "TOI",
    "TOI",
    "Hindu",
    "Vijayavani",
    "Deccan",
    "Hindu",
    "TOI",
    "TOI",
    "TOI, Prajavani, Mirror",
    "Prajavani",
    "VK",
    "Deccan, VK",
    "Vijayavani",
    "VK",
    "Mirror, TOI",
    "Salar, Deccan, Hindu",
    "Mirror, TOI (Sun - Deccan)",
    "Malayalam (Malabar)",
    "Deccan",
    "TOI, Mirror",
    "Prajavani",
    "Hindu, VK",
    "Prajavani, Kannada Prabha",
    "Hindu, ET (2nd floor)",
    "TOI",
    "TOI, ET, Vijayavani",
    "TOI",
    "TOI, Patrika",
    "TOI",
    "Vijayavani, Vijayavani",
    "Tamil (Thanti), Deccan",
    "TOI",
    "Vijayavani",
    "VK",
    "TOI (New Red Gate)",
    "TOI (New Masjid)",
    "TOI and ET (beside masjid)",
    "Deccan",
    "TOI, VK",
    "Vijayavani",
    "Prajavani, Hindu",
    "Prajavani, Prajavani",
    "Vijayavani",
    "Prajavani",
    "VK",
    "Tamil (Thanti), Kannada Prabha",
    "Hindu"
]


# --- Start Delivering with House-wise List ---
st.markdown("### 🏡 Houses to Deliver:")

# --- Initialize mark_all_houses_delivered flag
if "mark_all_houses_delivered" not in st.session_state:
    st.session_state.mark_all_houses_delivered = False

# --- Mark All / Clear All buttons for houses
col_houses1, col_houses2 = st.columns(2)

with col_houses1:
    if st.button("✅ Mark All Houses Delivered"):
        st.session_state.mark_all_houses_delivered = True
        st.rerun()

with col_houses2:
    if st.button("🗑️ Clear All Houses Delivered"):
        st.session_state.mark_all_houses_delivered = False
        st.rerun()

# --- Actual Houses Checkboxes ---
current_time = time.time()
total_to_deliver = len(house_papers_list)

col_left, col_right = st.columns(2)

for idx, papers in enumerate(house_papers_list, start=1):
    house_label = f"**House {idx}:** {papers}"

    address = f"House {idx}: {papers}"

    if address not in st.session_state.start_times:
        st.session_state.start_times[address] = current_time

    checkbox_key = f"delivery_{idx}"
    default_value = st.session_state.mark_all_houses_delivered

    if idx % 2 == 1:
        with col_left:
            delivered = st.checkbox(label=house_label, key=checkbox_key, value=st.session_state.get(checkbox_key, default_value))
    else:
        with col_right:
            delivered = st.checkbox(label=house_label, key=checkbox_key, value=st.session_state.get(checkbox_key, default_value))

    # 💥 Detect checkbox interaction
    if delivered and address not in st.session_state.completed_deliveries:
        st.session_state.completed_deliveries.add(address)
        st.session_state.completion_times[address] = time.time()
        st.rerun()  # 🚀 Rerun to refresh count immediately
    elif not delivered and address in st.session_state.completed_deliveries:
        st.session_state.completed_deliveries.remove(address)
        if address in st.session_state.completion_times:
            del st.session_state.completion_times[address]
        st.rerun()  # 🚀 Rerun to refresh count immediately




# --- Delivery Summary ---
remaining = total_to_deliver - len(st.session_state.completed_deliveries)
st.write(f"✅ Deliveries Completed: {len(st.session_state.completed_deliveries)}")
st.write(f"📦 Remaining: {remaining}")

if remaining == 0 and total_to_deliver > 0:
    st.success("🎯 All deliveries completed! 🎉")

    total_time_seconds = int(st.session_state.total_elapsed)

    if total_time_seconds < 60:
        total_time_display = f"{total_time_seconds} seconds"
    else:
        minutes = total_time_seconds // 60
        seconds = total_time_seconds % 60
        total_time_display = f"{minutes} minute{'s' if minutes > 1 else ''} {seconds} seconds"

    # ✅ Only total time display
    st.markdown(f"**🕒 Total Time for All Deliveries:** `{total_time_display}`")

    if st.button("🌟 Celebrate My Morning Hustle"):
        total_distance_km = 12  # fixed
        papers_collected = [paper for paper, collected in st.session_state.papers_collected.items() if collected]

        summary = generate_delivery_summary(
            len(st.session_state.completed_deliveries),
            total_distance_km,
            int(total_time_seconds // 60),
            papers_collected
        )
        st.success(summary)



    st.markdown("---")
    st.markdown("### 🔄 Reset Application")

# Add a small expander to show reset option neatly
with st.expander("Reset App (Clear all Data)?", expanded=False):
    if st.button("🔁 Confirm Reset"):
        st.session_state.clear()  # <-- Best way to wipe everything
        st.success("✅ Application has been reset successfully! Please refresh if needed.")
        st.rerun()
# Clean rerun