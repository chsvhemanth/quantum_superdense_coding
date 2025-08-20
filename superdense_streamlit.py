# superdense_streamlit.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
from io import BytesIO

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
def draw_circuit_small(qc, width=300):
    """Render circuit as PNG and return for Streamlit with fixed width."""
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

# Input selector
msg = st.radio("Choose 2 classical bits to send:", ["00","01","10","11"], horizontal=True)

if st.button("▶ Run Superdense Coding"):
    # Step 1: Show entanglement
    st.subheader("Step 1: Create Entangled Pair |Φ+⟩")
    buf, w = draw_circuit_small(create_bell_pair())
    st.image(buf, width=w)

    # Step 2: Encoding
    st.subheader(f"Step 2: Alice Encodes Message {msg}")
    qc_enc = create_bell_pair()
    encode_message(qc_enc, 1, msg)
    buf, w = draw_circuit_small(qc_enc)
    st.image(buf, width=w)

    # Step 3: Sending
    st.subheader("Step 3: Alice Sends Her Qubit to Bob")
    st.info("🚀 Alice’s qubit is transmitted to Bob (only 1 qubit is sent).")

    # Step 4: Decoding
    st.subheader("Step 4: Bob Applies Decoding (CNOT → H)")
    qc_dec = create_bell_pair()
    encode_message(qc_dec, 1, msg)
    decode_message(qc_dec)
    buf, w = draw_circuit_small(qc_dec)
    st.image(buf, width=w)

    # Step 5: Measurement
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
