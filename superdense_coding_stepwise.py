# superdense_stepwise_streamlit.py
import time
from io import BytesIO

import matplotlib.pyplot as plt
import streamlit as st
from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram

# ------------------------------------------
# Robust simulator selection (works on Cloud)
# ------------------------------------------
def simulate_counts(qc, shots=1000):
    """
    Try AerSimulator first; if not available (e.g., Streamlit Cloud),
    fall back to qasm_simulator from Aer or BasicAer.
    """
    try:
        from qiskit_aer import AerSimulator  # preferred
        sim = AerSimulator()
        compiled = transpile(qc, sim)
        job = sim.run(compiled, shots=shots)
        return job.result().get_counts()
    except Exception:
        try:
            # Older/newer distributions with Aer provider
            from qiskit import Aer
            backend = Aer.get_backend("qasm_simulator")
            compiled = transpile(qc, backend)
            job = backend.run(compiled, shots=shots)
            return job.result().get_counts()
        except Exception:
            # Basic Aer fallback (pure Python)
            from qiskit.providers.basicaer import QasmSimulator
            backend = QasmSimulator()
            compiled = transpile(qc, backend)
            job = backend.run(compiled, shots=shots)
            return job.result().get_counts()

# -----------------------------
# Step-wise circuit construction
# -----------------------------
def build_circuit_stepwise(msg: str, upto_step: int) -> QuantumCircuit:
    """
    Build the superdense coding circuit gate-by-gate.
    Steps:
      1: H on qubit 1
      2: CX(1, 0)  -> create Bell pair
      3: barrier   -> separate entanglement & encoding
      4: X(1) if msg[1] == '1'
      5: Z(1) if msg[0] == '1'
      6: barrier   -> 'sending' visualization
      7: CX(1, 0)  -> decode (CNOT)
      8: H(1)      -> decode (Hadamard)
      9: measure_all()
    """
    qc = QuantumCircuit(2)

    if upto_step >= 1:
        qc.h(1)
    if upto_step >= 2:
        qc.cx(1, 0)
    if upto_step >= 3:
        qc.barrier()

    # Encoding on Alice's qubit (1)
    if upto_step >= 4 and msg[1] == "1":
        qc.x(1)
    if upto_step >= 5 and msg[0] == "1":
        qc.z(1)

    if upto_step >= 6:
        qc.barrier()

    # Decoding at Bob
    if upto_step >= 7:
        qc.cx(1, 0)
    if upto_step >= 8:
        qc.h(1)

    if upto_step >= 9:
        qc.measure_all()

    return qc

# -----------------------------
# Drawing helper (small images)
# -----------------------------
def draw_circuit_small(qc: QuantumCircuit, width: int = 360):
    """Render circuit to PNG bytes, then let Streamlit control display width."""
    fig = qc.draw("mpl")
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf, width

# -----------------------------
# UI Helpers
# -----------------------------
STEP_TITLES = {
    1: "Apply H on qubit 1",
    2: "Create Bell pair with CNOT (control 1 → target 0)",
    3: "Barrier (separate entanglement and encoding)",
    4: "Encoding — apply X on qubit 1 if bit₂ = 1",
    5: "Encoding — apply Z on qubit 1 if bit₁ = 1",
    6: "Barrier (visualize sending Alice's qubit to Bob)",
    7: "Decoding — Bob applies CNOT (1 → 0)",
    8: "Decoding — Bob applies H on qubit 1",
    9: "Measure both qubits",
}

def next_button_label(current_step: int, msg: str) -> str:
    """Contextual label for the next step button."""
    nxt = current_step + 1
    if nxt in STEP_TITLES:
        return f"▶ Next: {STEP_TITLES[nxt]}"
    return "▶ Next"

def tiny_transition(duration: float = 0.8, updates: int = 24):
    """Simple progress animation."""
    prog = st.progress(0)
    for i in range(updates + 1):
        time.sleep(duration / updates)
        prog.progress(i / updates)
    time.sleep(0.05)

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="Superdense Coding — Step-by-Step", layout="wide")
st.title("🔮 Superdense Coding — Step-by-Step Reveal")

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
    total_steps = 9
    current = max(0, min(st.session_state.step, total_steps))
    st.write(f"**Progress:** Step {current} / {total_steps}")
    st.progress(current / total_steps)

st.divider()

# CURRENT VIEW: show circuit up to current step (if any)
current_step = st.session_state.step
if current_step > 0:
    st.subheader(f"Step {current_step}: {STEP_TITLES[current_step]}")
    qc_now = build_circuit_stepwise(msg, current_step)
    buf, w = draw_circuit_small(qc_now, width=380)
    st.image(buf, width=w)

# NEXT STEP BUTTON
if current_step < total_steps:
    if st.button(next_button_label(current_step, msg), type="primary"):
        with st.spinner("Applying next gate..."):
            tiny_transition(0.9, 28)
        st.session_state.step += 1
        st.rerun()

# FINAL RESULTS WHEN COMPLETE
if current_step >= total_steps:
    st.success("✅ Circuit complete — measuring and decoding results.")
    qc_full = build_circuit_stepwise(msg, total_steps)
    # Show final circuit small
    buf, w = draw_circuit_small(qc_full, width=380)
    st.image(buf, width=w)

    # Simulate & show counts + histogram
    counts = simulate_counts(qc_full, shots=1000)

    st.subheader("📊 Measurement Results")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.write("Counts:")
        st.json(counts)
    with c2:
        fig, ax = plt.subplots(figsize=(3, 2))
        plot_histogram(counts, ax=ax)
        st.pyplot(fig, clear_figure=True)

    decoded = max(counts, key=counts.get)
    st.success(f"🎯 Bob decodes the message as **{decoded}**")
