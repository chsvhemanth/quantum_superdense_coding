# dual_superdense_vs_classical_streamlit_enhanced.py
"""
Enhanced Streamlit app:
- UI/UX improvements (sync steps, cards, better layout)
- Analytics & Learning (noise sweep, Monte-Carlo success probability, efficiency metrics)
- Exportable results (JSON, circuit PNG)
Notes:
- Noise model used here is a simple educational approximation (bit flips applied to
  transmitted bits / measurements). For production-grade noise modeling use qiskit's
  noise module and real backends.
"""
import time
import json
from io import BytesIO
from functools import lru_cache

import matplotlib.pyplot as plt
import streamlit as st

# Quantum Libraries
from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram

# Classical (flowchart)
import networkx as nx
import numpy as np
import random

# ============== Quantum Helper Functions ==============

def simulate_counts(qc, shots=1000):
    """
    Run quantum circuit and return measurement counts.
    Tries AerSimulator, then Aer, then basic QasmSimulator.
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
    Qubit ordering kept same as user's original (qubit 1 is Alice's).
    """
    qc = QuantumCircuit(2, 2)
    # create bell pair (steps 1-2)
    if upto_step >= 1:
        qc.h(1)
    if upto_step >= 2:
        qc.cx(1, 0)
    if upto_step >= 3:
        qc.barrier()
    # encode on Alice's qubit (qubit 1)
    if upto_step >= 4 and msg[1] == "1":  # apply X if second bit = 1
        qc.x(1)
    if upto_step >= 5 and msg[0] == "1":  # apply Z if first bit = 1
        qc.z(1)
    if upto_step >= 6:
        qc.barrier()
    # decoding by Bob (apply CNOT then H)
    if upto_step >= 7:
        qc.cx(1, 0)
    if upto_step >= 8:
        qc.h(1)
    if upto_step >= 9:
        qc.measure(0, 0)
        qc.measure(1, 1)
    return qc


def draw_circuit_small(qc: QuantumCircuit, width: int = 360):
    fig = qc.draw("mpl")
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf, width

# ============== Classical Helper Functions ==============

def classical_encode(msg: str):
    """Simple repetition: duplicate each bit once."""
    return "".join([bit * 2 for bit in msg])


def classical_decode(encoded: str):
    """Decode the repetition code by majority per pair (tie -> first bit)."""
    decoded_bits = []
    for i in range(0, len(encoded), 2):
        pair = encoded[i:i + 2]
        # majority vote
        if pair.count('1') >= 1.5:
            decoded_bits.append('1')
        else:
            # if exactly 1 or zero, fallback to first bit as earlier behavior
            decoded_bits.append('1' if pair.count('1') > 1 else pair[0])
    return "".join(decoded_bits)


def draw_classical_flow(msg, encoded=None, received=None, decoded=None, step=1):
    """Draw simple directional flowchart, displayed via st.pyplot."""
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

# ================ UI STEPS / Titles ================

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
    6: "Decoding Step 1: Check for errors (parity)",
    7: "Decoding Step 2: Correct errors if any",
    8: "Output: Decoded 2-bit message",
}

def tiny_transition(duration: float = 0.6, updates: int = 20):
    prog = st.progress(0)
    for i in range(updates + 1):
        time.sleep(duration / updates)
        prog.progress(i / updates)
    time.sleep(0.05)

# ================ Utility: simple noise models (educational) ================

def flip_bits_string(s: str, p: float):
    """Flip each bit in string s independently with probability p."""
    out = []
    for ch in s:
        if random.random() < p:
            out.append('1' if ch == '0' else '0')
        else:
            out.append(ch)
    return "".join(out)


def apply_quantum_measurement_noise(measured: str, p: float):
    """
    Educational approximation: flip each measured bit with probability p.
    (In real quantum noise models, errors are on qubits and affect decoding differently.)
    """
    return flip_bits_string(measured, p)


# ================ Streamlit Layout ================

st.set_page_config(page_title="Quantum vs Classical — Enhanced", layout="wide")
st.title("⚡ Superdense (Quantum) vs Classical 2-bit Transmission — Enhanced UI & Analytics")

# Sidebar controls
with st.sidebar:
    st.header("Controls & Learning Tools")
    msg = st.radio("Choose 2-bit message (b₁ b₂):", ["00", "01", "10", "11"], horizontal=True)
    st.markdown("**Noise & Simulation**")
    noise_enabled = st.checkbox("Enable noisy channel (educational)", value=False,
                                help="Toggle to inject random bit flips into the transmission.")
    noise_prob = st.slider("Noise probability (p)", min_value=0.0, max_value=0.5, value=0.05, step=0.01,
                           help="Probability each transmitted/measured bit flips. Educational demo.")
    batch_sim_runs = st.number_input("Monte-Carlo runs for analytics", min_value=200, max_value=5000, value=800, step=100)
    st.markdown("---")
    st.checkbox("Sync steps (advance both sides together)", key="sync_steps", value=False)
    st.markdown("**Export & Backend**")
    enable_export = st.checkbox("Show export options", value=True)
    use_ibm = st.checkbox("Enable IBM Quantum backend (requires API key)", value=False)
    if use_ibm:
        ibm_token = st.text_input("IBMQ API Token", type="password")
    else:
        ibm_token = None
    st.markdown("---")
    st.markdown("**Help / Hints**")
    st.info("Use Next buttons to advance stepwise. Use Sync Steps to advance both simultaneously for direct comparison.")

# Step/session management
if "step_q" not in st.session_state:
    st.session_state.step_q = 0
if "step_c" not in st.session_state:
    st.session_state.step_c = 0
if "last_msg" not in st.session_state:
    st.session_state.last_msg = "00"
if "analytics_cache" not in st.session_state:
    st.session_state.analytics_cache = {}

# Reset steps if message changed
if st.session_state.last_msg != msg:
    st.session_state.step_q = 0
    st.session_state.step_c = 0
    st.session_state.last_msg = msg

# Top metrics row
top_cols = st.columns([2, 1, 1])
with top_cols[0]:
    st.subheader("Overview")
    st.write("Compare how superdense coding (quantum) packs 2 classical bits into 1 qubit (with entanglement) vs a simple classical repetition code.")
with top_cols[1]:
    bits_sent_classical = len(classical_encode(msg))
    bits_sent_quantum = 1  # we physically send 1 qubit (Alice's)
    st.metric("Bits sent (classical)", f"{bits_sent_classical} bits")
with top_cols[2]:
    st.metric("Qubits sent (quantum)", f"{bits_sent_quantum} qubit")

st.markdown("---")

# Dual columns for Quantum and Classical with cards
qcol, ccol = st.columns(2)

# ----------- Quantum Side (Left/Column 1) -----------
with qcol:
    st.header("🔮 Quantum: Superdense Coding (Stepwise)")
    total_steps_q = len(QUANTUM_STEP_TITLES)
    st.write(f"**Quantum Step:** {st.session_state.step_q} / {total_steps_q}")
    st.progress(st.session_state.step_q / total_steps_q)

    # Restart / Step controls
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("🔄 Restart Quantum", key="q_restart"):
            st.session_state.step_q = 0
    with c2:
        if st.button("⏹ Reset Both", key="both_reset"):
            st.session_state.step_q = 0
            st.session_state.step_c = 0
    with c3:
        # Next step: consider sync
        next_label = QUANTUM_STEP_TITLES.get(st.session_state.step_q + 1, '')
        if st.button(f"➡ Next Quantum: {next_label}", key="q_next"):
            with st.spinner("Applying next quantum gate..."):
                tiny_transition(0.7)
            st.session_state.step_q += 1
            if st.session_state.get("sync_steps", False):
                st.session_state.step_c = min(st.session_state.step_c + 1, len(CLASSICAL_STEP_TITLES))
            st.rerun()

    if st.session_state.step_q > 0:
        st.subheader(f"Step {st.session_state.step_q}: {QUANTUM_STEP_TITLES[st.session_state.step_q]}")
        qc_now = build_circuit_stepwise(msg, st.session_state.step_q)
        buf, w = draw_circuit_small(qc_now, width=370)
        st.image(buf, width=w)

    if st.session_state.step_q >= total_steps_q:
        st.success("✅ Quantum circuit complete — measuring and decoding results.")
        qc_full = build_circuit_stepwise(msg, total_steps_q)
        buf, w = draw_circuit_small(qc_full, width=380)
        st.image(buf, width=w)

        counts = simulate_counts(qc_full, shots=1024)
        st.subheader("📊 Quantum Measurement Results (raw counts)")
        q1, q2 = st.columns(2)
        with q1:
            st.write("Counts:")
            st.json(counts)
        with q2:
            fig, ax = plt.subplots(figsize=(3, 2))
            plot_histogram(counts, ax=ax)
            st.pyplot(fig)
            plt.close(fig)

        # Most frequent measured bitstring -> interpret as decoded message
        decoded_meas = max(counts, key=counts.get)  # format like '01' but depends on ordering
        # Ensure bit ordering aligns with classical expectation (we measured qc.measure(0,0) then qc.measure(1,1))
        # The string key from Qiskit is "b1 b0"? Usually keys are little-endian like '01' => bit1=0 bit0=1
        # For teaching simplicity, we'll use counts directly and present to user
        st.success(f"🎯 Quantum most frequent measurement: **{decoded_meas}**")

        # Apply optional measurement noise (educational)
        if noise_enabled:
            noisy = apply_quantum_measurement_noise(decoded_meas, noise_prob)
            st.write(f"With noise p={noise_prob:.2f} → noisy measurement: {noisy}")
            final_quantum_decoded = noisy
        else:
            final_quantum_decoded = decoded_meas

        st.info("Note: Qiskit measurement string ordering depends on backend. Use counts to inspect mapping.")
        # Offer download of circuit image
        if enable_export:
            st.download_button("Download circuit PNG", data=buf, file_name="superdense_circuit.png", mime="image/png")

# ----------- Classical Side (Right/Column 2) -----------
with ccol:
    st.header("🔢 Classical: Bitwise Encoding (Stepwise)")
    total_steps_c = len(CLASSICAL_STEP_TITLES)
    st.write(f"**Classical Step:** {st.session_state.step_c} / {total_steps_c}")
    st.progress(st.session_state.step_c / total_steps_c)

    # Restart / Next controls
    cc1, cc2 = st.columns([1, 1])
    with cc1:
        if st.button("🔄 Restart Classical", key="c_restart"):
            st.session_state.step_c = 0
    with cc2:
        next_label_c = CLASSICAL_STEP_TITLES.get(st.session_state.step_c + 1, '')
        if st.button(f"➡ Next Classical: {next_label_c}", key="c_next"):
            with st.spinner("Processing next classical step..."):
                tiny_transition(0.7)
            st.session_state.step_c += 1
            if st.session_state.get("sync_steps", False):
                st.session_state.step_q = min(st.session_state.step_q + 1, len(QUANTUM_STEP_TITLES))
            st.rerun()

    encoded = classical_encode(msg)
    # Inject noise into the transmitted bits if enabled
    if noise_enabled:
        received = flip_bits_string(encoded, noise_prob)
    else:
        received = encoded
    decoded = classical_decode(received)

    if st.session_state.step_c > 0:
        st.subheader(f"Step {st.session_state.step_c}: {CLASSICAL_STEP_TITLES[st.session_state.step_c]}")
        draw_classical_flow(msg, encoded, received, decoded, st.session_state.step_c)

    if st.session_state.step_c >= total_steps_c:
        st.success(f"✅ Classical encoding and decoding complete!")
        st.write(f"**Original:** {msg}  •  **Encoded:** {encoded}  •  **Received:** {received}  •  **Decoded:** {decoded}")
        if msg == decoded:
            st.balloons()
            st.success("🎉 Decoding successful! Message correctly recovered.")
        else:
            st.error("⚠️ Decoding error: Message corrupted.")

# ================ Analytics & Learning Section ================
st.markdown("---")
st.header("📊 Analytics & Learning")

analytics_col1, analytics_col2 = st.columns([2, 1])

with analytics_col1:
    st.subheader("Success probability vs Noise (Monte-Carlo)")
    st.write("Run a batch simulation to estimate the probability that each scheme recovers the original 2-bit message correctly as noise increases.")
    run_analytics = st.button("Run Monte-Carlo Analytics", key="run_analytics")

    # Optionally reuse cached results for the same parameters
    cache_key = f"{msg}_{batch_sim_runs}"
    if run_analytics or cache_key not in st.session_state.analytics_cache:
        # Run simulations: sweep over p values
        ps = np.linspace(0.0, 0.3, 13)  # 0% to 30% noise for demo
        classical_success = []
        quantum_success = []
        runs = int(batch_sim_runs)

        progress_bar = st.progress(0)
        for i, p in enumerate(ps):
            correct_c = 0
            correct_q = 0
            for _ in range(runs):
                # classical: encode -> flip bits with probability p -> decode
                encoded_c = classical_encode(msg)
                received_c = flip_bits_string(encoded_c, p)
                decoded_c = classical_decode(received_c)
                if decoded_c == msg:
                    correct_c += 1

                # quantum: educational approx - take ideal decoded (msg), flip each of its two bits with prob p
                # (This is just a demonstration; proper quantum noise simulation requires channel on qubit.)
                measured = msg  # ideal decode from a perfect quantum channel
                noisy_meas = flip_bits_string(measured, p)
                if noisy_meas == msg:
                    correct_q += 1

            classical_success.append(correct_c / runs)
            quantum_success.append(correct_q / runs)
            progress_bar.progress((i + 1) / len(ps))
        st.session_state.analytics_cache[cache_key] = {
            "ps": ps.tolist(),
            "classical_success": classical_success,
            "quantum_success": quantum_success
        }
        st.success(f"Monte-Carlo done ({runs} runs per p).")
    else:
        st.info("Using cached analytics results.")
    data = st.session_state.analytics_cache[cache_key]
    ps = np.array(data["ps"])
    cs = np.array(data["classical_success"])
    qs = np.array(data["quantum_success"])

    # Plot the success vs noise
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(ps, cs, marker='o', label='Classical (repetition)')
    ax.plot(ps, qs, marker='o', linestyle='--', label='Quantum (educational approx)')
    ax.set_xlabel("Noise probability p")
    ax.set_ylabel("Success probability")
    ax.set_title("Success vs Noise")
    ax.set_ylim(-0.02, 1.02)
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

with analytics_col2:
    st.subheader("Efficiency Metrics")
    # Efficiency: classical sends 4 bits to encode 2 bits? Our repetition sends 4? For 2-bit message, repetition => length=4
    sent_bits = len(classical_encode(msg))
    effective_information = 2  # original message length
    classical_efficiency = effective_information / sent_bits
    quantum_efficiency = effective_information / 1.0  # 2 bits conveyed by sending 1 qubit (theoretical)
    st.metric("Classical efficiency (info/sent)", f"{classical_efficiency:.2f}")
    st.metric("Quantum efficiency (info/qubit)", f"{quantum_efficiency:.2f}")

    # small bar chart
    fig2, ax2 = plt.subplots(figsize=(3, 2))
    ax2.bar(["Classical", "Quantum"], [classical_efficiency, quantum_efficiency])
    ax2.set_ylim(0, 2.2)
    ax2.set_ylabel("Information per physical unit")
    st.pyplot(fig2)
    plt.close(fig2)

# ================ Export / Download ================
st.markdown("---")
st.header("💾 Export & Share")

export_col1, export_col2 = st.columns([2, 1])
with export_col1:
    if enable_export:
        # Prepare a short JSON report
        report = {
            "message": msg,
            "classical": {
                "encoded": classical_encode(msg),
                "received": received,
                "decoded": decoded
            },
            "quantum": {
                "measurement_counts": (counts if 'counts' in locals() else {}),
                "most_frequent": (decoded_meas if 'decoded_meas' in locals() else "")
            },
            "noise": {
                "enabled": noise_enabled,
                "probability": float(noise_prob)
            },
            "analytics": st.session_state.analytics_cache.get(cache_key, {})
        }
        report_bytes = json.dumps(report, indent=2).encode()
        st.download_button("Download report (JSON)", data=report_bytes, file_name="transmission_report.json", mime="application/json")

        # If qc_full exists, allow png download
        if 'qc_full' in locals():
            buf2, _ = draw_circuit_small(qc_full, width=640)
            st.download_button("Download quantum circuit (PNG)", data=buf2, file_name="superdense_full.png", mime="image/png")
    else:
        st.info("Enable 'Show export options' in sidebar to see export controls.")

with export_col2:
    st.subheader("Share")
    st.write("You can copy the JSON report or PNG file and share with others. For reproducible experiments, include the random-seed and backend info.")

# ================ Advanced: Optional IBM Backend (placeholder) ================
st.markdown("---")
if use_ibm and ibm_token:
    st.info("IBM backend requested — note: this section is a placeholder. Implement IBMQ enablement with qiskit_ibm_runtime or qiskit.providers.ibmq.")
    # For safety, we avoid automatically logging in. This is a stub to guide the user.
    st.write("To enable real-device runs: use qiskit_ibm_provider or qiskit-ibm-runtime with your token, select a backend and submit jobs.")
else:
    if use_ibm:
        st.warning("Enable IBMQ by providing a token in the sidebar to see options.")

st.markdown("---")
st.caption("Educational demo: quantum noise is approximated for clarity. For high-fidelity experiments use Qiskit's noise models and real backends.")

# ================ End of App ================
