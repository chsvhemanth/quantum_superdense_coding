# dual_superdense_vs_classical_streamlit.py

import time
from io import BytesIO
import matplotlib.pyplot as plt
import streamlit as st

# Quantum Libraries
from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram

# Classical (flowchart)
import networkx as nx

# ============== Quantum Helper Functions ==============

def simulate_counts(qc, shots=1000):
    """
    Run quantum circuit and return measurement counts.
    Supports multiple simulator fallbacks for cloud/local.
    """
    try:
        from qiskit_aer import AerSimulator
        sim = AerSimulator()
        compiled = transpile(qc, sim)
        job = sim.run(compiled, shots=shots)
        return job.result().get_counts()
    except Exception:
        try:
            from qiskit import Aer
            backend = Aer.get_backend("qasm_simulator")
            compiled = transpile(qc, backend)
            job = backend.run(compiled, shots=shots)
            return job.result().get_counts()
        except Exception:
            from qiskit.providers.basicaer import QasmSimulator
            backend = QasmSimulator()
            compiled = transpile(qc, backend)
            job = backend.run(compiled, shots=shots)
            return job.result().get_counts()


def build_circuit_stepwise(msg: str, upto_step: int) -> QuantumCircuit:
    """
    Build the superdense circuit up to the given step.
    """
    qc = QuantumCircuit(2)
    if upto_step >= 1:
        qc.h(1)
    if upto_step >= 2:
        qc.cx(1, 0)
    if upto_step >= 3:
        qc.barrier()
    if upto_step >= 4 and msg[1] == "1":
        qc.x(1)
    if upto_step >= 5 and msg[0] == "1":   # ✅ fixed indexing bug here
        qc.z(1)
    if upto_step >= 6:
        qc.barrier()
    if upto_step >= 7:
        qc.cx(1, 0)
    if upto_step >= 8:
        qc.h(1)
    if upto_step >= 9:
        qc.measure_all()
    return qc


def draw_circuit_small(qc: QuantumCircuit, width: int = 360):
    fig = qc.draw("mpl")
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return buf, width

# ============== Classical Helper Functions ==============

def classical_encode(msg: str):
    return "".join([bit * 2 for bit in msg])


def classical_decode(encoded: str):
    decoded_bits = []
    for i in range(0, len(encoded), 2):
        pair = encoded[i:i + 2]
        decoded_bits.append('1' if pair.count('1') > 1 else pair[0])
    return "".join(decoded_bits)


def draw_classical_flow(msg, encoded=None, received=None, decoded=None, step=1):
    G = nx.DiGraph()
    if step >= 1:
        G.add_node(f"Input\n{msg}", pos=(0, 0))
    if step >= 2:
        G.add_node("Codeword\n(combine bits)", pos=(1, 0))
        G.add_edge(f"Input\n{msg}", "Codeword\n(combine bits)")
    if step >= 3:
        G.add_node(f"Encoded\n{encoded}", pos=(2, 0))
        G.add_edge("Codeword\n(combine bits)", f"Encoded\n{encoded}")
    if step >= 4:
        G.add_node("Transmit\n(bits sent)", pos=(3, 0))
        G.add_edge(f"Encoded\n{encoded}", "Transmit\n(bits sent)")
    if step >= 5:
        G.add_node(f"Received\n{received}", pos=(4, 0))
        G.add_edge("Transmit\n(bits sent)", f"Received\n{received}")
    if step >= 6:
        G.add_node("Check errors\n(parity)", pos=(5, 0))
        G.add_edge(f"Received\n{received}", "Check errors\n(parity)")
    if step >= 7:
        G.add_node(f"Corrected\n{decoded}", pos=(6, 0))
        G.add_edge("Check errors\n(parity)", f"Corrected\n{decoded}")
    if step >= 8:
        G.add_node(f"Output\n{decoded}", pos=(7, 0))
        G.add_edge(f"Corrected\n{decoded}", f"Output\n{decoded}")

    pos = nx.get_node_attributes(G, 'pos')
    fig, ax = plt.subplots(figsize=(10, 2))
    nx.draw(G, pos, with_labels=True, node_size=2500, node_color="skyblue",
            font_size=9, font_weight="bold", arrowsize=20, ax=ax)
    plt.axis('off')
    st.pyplot(fig)
    plt.close(fig)

# ================ UI STEPS ================

QUANTUM_STEP_TITLES = {
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

CLASSICAL_STEP_TITLES = {
    1: "Input: Original 2-bit message",
    2: "Encoding Step 1: Combine bits into a codeword",
    3: "Encoding Step 2: Apply classical encoding (repetition code)",
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

# ================ Streamlit Layout ================

st.set_page_config(page_title="Quantum vs Classical Encoding — Stepwise Comparison", layout="wide")
st.title("⚡ Side-by-Side: Superdense (Quantum) vs Classical 2-bit Transmission")

# Step/session management
if "step_q" not in st.session_state:
    st.session_state.step_q = 0
if "step_c" not in st.session_state:
    st.session_state.step_c = 0
if "last_msg" not in st.session_state:
    st.session_state.last_msg = "00"

msg = st.radio("Choose 2 bits to send (b₁ b₂):", ["00", "01", "10", "11"], horizontal=True)

# Reset steps if message changed
if st.session_state.last_msg != msg:
    st.session_state.step_q = 0
    st.session_state.step_c = 0
    st.session_state.last_msg = msg

# Dual columns for Quantum and Classical
qcol, ccol = st.columns(2)

# ----------- Quantum Side (Left/Column 1) -----------
with qcol:
    st.header("🔮 Quantum: Superdense Coding (Stepwise)")
    total_steps_q = len(QUANTUM_STEP_TITLES)
    if st.button("🔄 Restart Quantum", key="q_restart"):
        st.session_state.step_q = 0
    st.write(f"**Quantum Step:** {st.session_state.step_q} / {total_steps_q}")
    st.progress(st.session_state.step_q / total_steps_q)

    if st.session_state.step_q > 0:
        st.subheader(f"Step {st.session_state.step_q}: {QUANTUM_STEP_TITLES[st.session_state.step_q]}")
        qc_now = build_circuit_stepwise(msg, st.session_state.step_q)
        buf, w = draw_circuit_small(qc_now, width=370)
        st.image(buf, width=w)

    if st.session_state.step_q < total_steps_q:
        if st.button(f"➡ Next Quantum: {QUANTUM_STEP_TITLES.get(st.session_state.step_q+1, '')}", key="q_next", type="primary"):
            with st.spinner("Applying next quantum gate..."):
                tiny_transition(0.9, 28)
            st.session_state.step_q += 1
            st.rerun()   # ✅ updated

    # Final results
    if st.session_state.step_q >= total_steps_q:
        st.success("✅ Quantum circuit complete — measuring and decoding results.")
        qc_full = build_circuit_stepwise(msg, total_steps_q)
        buf, w = draw_circuit_small(qc_full, width=380)
        st.image(buf, width=w)

        counts = simulate_counts(qc_full, shots=1000)
        st.subheader("📊 Quantum Measurement Results")
        q1, q2 = st.columns(2)
        with q1:
            st.write("Counts:")
            st.json(counts)
        with q2:
            fig, ax = plt.subplots(figsize=(3, 2))
            plot_histogram(counts, ax=ax)
            st.pyplot(fig)
            plt.close(fig)

        decoded = max(counts, key=counts.get)
        st.success(f"🎯 Quantum result decoded as: **{decoded}**")

# ----------- Classical Side (Right/Column 2) -----------
with ccol:
    st.header("🔢 Classical: Bitwise Encoding (Stepwise)")
    total_steps_c = len(CLASSICAL_STEP_TITLES)
    if st.button("🔄 Restart Classical", key="c_restart"):
        st.session_state.step_c = 0
    st.write(f"**Classical Step:** {st.session_state.step_c} / {total_steps_c}")
    st.progress(st.session_state.step_c / total_steps_c)

    encoded = classical_encode(msg)
    received = encoded  # No errors for baseline demo
    decoded = classical_decode(received)

    if st.session_state.step_c > 0:
        st.subheader(f"Step {st.session_state.step_c}: {CLASSICAL_STEP_TITLES[st.session_state.step_c]}")
        draw_classical_flow(msg, encoded, received, decoded, st.session_state.step_c)

    if st.session_state.step_c < total_steps_c:
        if st.button(f"➡ Next Classical: {CLASSICAL_STEP_TITLES.get(st.session_state.step_c+1, '')}", key="c_next", type="primary"):
            with st.spinner("Processing next classical step..."):
                tiny_transition(0.9, 28)
            st.session_state.step_c += 1
            st.rerun()   # ✅ updated

    if st.session_state.step_c >= total_steps_c:
        st.success(f"✅ Classical encoding and decoding complete!\n\n**Original:** {msg}\n**Encoded:** {encoded}\n**Received:** {received}\n**Decoded:** {decoded}")
        if msg == decoded:
            st.balloons()
            st.success("🎉 Decoding successful! Message correctly recovered.")
        else:
            st.error("⚠️ Decoding error: Message corrupted.")

# ============= End of App =============
