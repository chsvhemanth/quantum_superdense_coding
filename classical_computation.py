# classical_stepwise_streamlit.py
import time
import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx

# -----------------------------
# Stepwise classical encoding/decoding
# -----------------------------

STEP_TITLES = {
    1: "Input: Original 2-bit message",
    2: "Encoding Step 1: Combine bits into a codeword",
    3: "Encoding Step 2: Apply classical encoding (e.g., repetition or parity bit)",
    4: "Transmitting encoded bits over the channel",
    5: "Receiving encoded bits",
    6: "Decoding Step 1: Check for errors (parity check)",
    7: "Decoding Step 2: Correct errors if any",
    8: "Output: Decoded 2-bit message",
}

def tiny_transition(duration: float = 0.8, updates: int = 24):
    prog = st.progress(0)
    for i in range(updates + 1):
        time.sleep(duration / updates)
        prog.progress(i / updates)
    time.sleep(0.05)

def classical_encode(msg: str):
    # Example: simple repetition code - repeat each bit twice
    encoded = "".join([bit*2 for bit in msg])
    return encoded

def classical_decode(encoded: str):
    # Majority voting decoding on pairs
    decoded_bits = []
    for i in range(0, len(encoded), 2):
        pair = encoded[i:i+2]
        # simple majority vote, since bits repeated twice, just pick first (or majority)
        decoded_bits.append('1' if pair.count('1') > 1 else pair[0])
    return "".join(decoded_bits)

def draw_classical_flow(msg, encoded=None, received=None, decoded=None, step=1):
    """
    Draw a simple classical flow diagram for encoding/decoding using networkx.
    """
    G = nx.DiGraph()
    
    if step >= 1:
        G.add_node("Input\nMessage\n" + msg, pos=(0, 0))
    if step >= 2:
        G.add_node("Codeword (combine bits)", pos=(1, 0))
        G.add_edge("Input\nMessage\n" + msg, "Codeword (combine bits)")
    if step >= 3:
        G.add_node(f"Encoded\n{encoded}", pos=(2, 0))
        G.add_edge("Codeword (combine bits)", f"Encoded\n{encoded}")
    if step >= 4:
        G.add_node("Transmit\n(bits sent)", pos=(3, 0))
        G.add_edge(f"Encoded\n{encoded}", "Transmit\n(bits sent)")
    if step >= 5:
        G.add_node(f"Received\n{received}", pos=(4, 0))
        G.add_edge("Transmit\n(bits sent)", f"Received\n{received}")
    if step >= 6:
        G.add_node("Check errors\n(e.g., parity)", pos=(5, 0))
        G.add_edge(f"Received\n{received}", "Check errors\n(e.g., parity)")
    if step >= 7:
        G.add_node(f"Corrected\n{decoded}", pos=(6, 0))
        G.add_edge("Check errors\n(e.g., parity)", f"Corrected\n{decoded}")
    if step >= 8:
        G.add_node("Output\nMessage\n" + decoded, pos=(7, 0))
        G.add_edge(f"Corrected\n{decoded}", "Output\nMessage\n" + decoded)

    pos = nx.get_node_attributes(G, 'pos')
    plt.figure(figsize=(12, 2))
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=10, font_weight="bold", arrowsize=20)
    st.pyplot(plt.gcf())
    plt.clf()

# -----------------------------
# Streamlit App
# -----------------------------

st.set_page_config(page_title="Classical Encoding — Step-by-Step", layout="wide")
st.title("🔢 Classical 2-Bit Encoding and Decoding — Step-by-Step Reveal")

# Session state
if "step" not in st.session_state:
    st.session_state.step = 0
if "last_msg" not in st.session_state:
    st.session_state.last_msg = "00"

# Inputs
msg = st.radio("Choose 2 classical bits (b₁ b₂):", ["00", "01", "10", "11"], horizontal=True)

# Auto-reset if the message changed
if st.session_state.last_msg != msg:
    st.session_state.step = 0
    st.session_state.last_msg = msg

# Controls row
left, right = st.columns([1, 1])
with left:
    if st.button("🔄 Restart"):
        st.session_state.step = 0
with right:
    total_steps = len(STEP_TITLES)
    current = max(0, min(st.session_state.step, total_steps))
    st.write(f"**Progress:** Step {current} / {total_steps}")
    st.progress(current / total_steps)

st.divider()

current_step = st.session_state.step

encoded = classical_encode(msg)
received = encoded  # for simplicity, assume no errors
decoded = classical_decode(received)

if current_step > 0:
    st.subheader(f"Step {current_step}: {STEP_TITLES[current_step]}")

# Show visualization per step
draw_classical_flow(msg, encoded, received, decoded, current_step)

if current_step < total_steps:
    if st.button(f"▶ Next: {STEP_TITLES.get(current_step + 1, '')}", type="primary"):
        with st.spinner("Processing next step..."):
            tiny_transition(0.9, 28)
        st.session_state.step += 1
        # No explicit rerun needed; Streamlit auto reruns on state change

if current_step >= total_steps:
    st.success("✅ Classical encoding and decoding complete.")
    st.write(f"**Original message:** {msg}")
    st.write(f"**Encoded message:** {encoded}")
    st.write(f"**Received message:** {received}")
    st.write(f"**Decoded message:** {decoded}")

    if msg == decoded:
        st.balloons()
        st.success("🎉 Decoding successful! Message correctly recovered.")
    else:
        st.error("⚠️ Decoding error: message corrupted.")
