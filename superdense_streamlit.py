# superdense_streamlit.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
from io import BytesIO
import time

# -----------------------------
# Qiskit functions
# -----------------------------
def create_bell_pair():
    qc = QuantumCircuit(2)
    qc.h(1)
    qc.cx(1, 0)
    return qc

def encode_message(qc, qubit, msg):
    if msg[1] == "1":
        qc.x(qubit)
    if msg[0] == "1":
        qc.z(qubit)
    return qc

def decode_message(qc):
    qc.cx(1, 0)
    qc.h(1)
    return qc

def run_superdense(msg="00", shots=1000):
    qc = create_bell_pair()
    qc.barrier()
    encode_message(qc, 1, msg)
    qc.barrier()
    decode_message(qc)
    qc.measure_all()

    sim = AerSimulator()
    compiled = transpile(qc, sim)
    job = sim.run(compiled, shots=shots)
    result = job.result()
    counts = result.get_counts()
    return qc, counts

# -----------------------------
# Helper for smaller circuit plots
# -----------------------------
def draw_circuit_small(qc, width=350):
    fig = qc.draw("mpl")
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf, width

# -----------------------------
# Streamlit App
# -----------------------------
st.set_page_config(page_title="Superdense Coding Simulator", layout="wide")
st.title("🔮 Superdense Coding Demo (Qiskit + Streamlit)")

# Track steps in session_state
if "step" not in st.session_state:
    st.session_state.step = 0

# Input selector
msg = st.radio("Choose 2 classical bits to send:", ["00","01","10","11"], horizontal=True)

# Reset button
if st.button("🔄 Restart Simulation"):
    st.session_state.step = 0

# STEP 1
if st.session_state.step >= 1:
    st.subheader("Step 1: Create Entangled Pair |Φ+⟩")
    buf, w = draw_circuit_small(create_bell_pair())
    st.image(buf, width=w)
if st.session_state.step == 0:
    if st.button("▶ Start with Step 1"):
        st.session_state.step = 1
        st.rerun()

# STEP 2
if st.session_state.step >= 2:
    st.subheader(f"Step 2: Alice Encodes Message {msg}")
    qc_enc = create_bell_pair()
    encode_message(qc_enc, 1, msg)
    buf, w = draw_circuit_small(qc_enc)
    st.image(buf, width=w)
if st.session_state.step == 1:
    if st.button("➡ Next: Encoding"):
        with st.spinner("Applying encoding..."):
            time.sleep(1.2)  # transition effect
        st.session_state.step = 2
        st.rerun()

# STEP 3
if st.session_state.step >= 3:
    st.subheader("Step 3: Alice Sends Her Qubit to Bob")
    st.info("🚀 Alice’s qubit is transmitted to Bob (only 1 qubit is sent).")
if st.session_state.step == 2:
    if st.button("➡ Next: Transmission"):
        with st.spinner("Transmitting qubit..."):
            time.sleep(1.2)
        st.session_state.step = 3
        st.rerun()

# STEP 4
if st.session_state.step >= 4:
    st.subheader("Step 4: Bob Applies Decoding (CNOT → H)")
    qc_dec = create_bell_pair()
    encode_message(qc_dec, 1, msg)
    decode_message(qc_dec)
    buf, w = draw_circuit_small(qc_dec)
    st.image(buf, width=w)
if st.session_state.step == 3:
    if st.button("➡ Next: Decoding"):
        with st.spinner("Bob is decoding..."):
            time.sleep(1.2)
        st.session_state.step = 4
        st.rerun()

# STEP 5
if st.session_state.step >= 5:
    st.subheader("Step 5: Measurement")
    qc_final, counts = run_superdense(msg)
    buf, w = draw_circuit_small(qc_final)
    st.image(buf, width=w)

    # Results side by side
    st.subheader("📊 Measurement Results")
    col1, col2 = st.columns([1,1])
    with col1:
        st.write("Counts:")
        st.json(counts)
    with col2:
        fig, ax = plt.subplots(figsize=(3,2))
        plot_histogram(counts, ax=ax)
        st.pyplot(fig, clear_figure=True)

    # Final Output
    decoded = max(counts, key=counts.get)
    st.success(f"✅ Bob decodes the message as: **{decoded}**")
if st.session_state.step == 4:
    if st.button("➡ Next: Measurement"):
        with st.spinner("Measuring qubits..."):
            time.sleep(1.2)
        st.session_state.step = 5
        st.rerun()
