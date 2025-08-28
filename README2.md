# ⚡ Quantum vs Classical Encoding — Side-by-Side (Streamlit App)

This project is an **interactive educational tool** that compares **Quantum Superdense Coding** with **Classical Bitwise Transmission** step by step.  
It demonstrates how **two classical bits** can be transmitted using only **one qubit and shared entanglement** in the quantum case, while also showing the **classical repetition code approach** in parallel.

👉 **Live Demo:** [Quantum Superdense Coding and Classical Comparison App](https://quantumsuperdensecodingandclassicalcomparison.streamlit.app/)

This app builds upon our earlier prototype of [Superdense Coding — Step-by-Step](https://quantum-superdense-coding.streamlit.app/) by adding a **side-by-side comparison** of quantum and classical encoding, making it easier to see the efficiency gains of quantum communication.

---

## ✨ Features
- 🎭 **Dual column layout** — Quantum (left) vs Classical (right)  
- 🚀 **Interactive step-by-step exploration** with smooth transitions  
- 🔮 **Quantum side:** Circuit diagrams, gates, entanglement, encoding, and decoding  
- 🔢 **Classical side:** Encoding, transmission, error checking, and decoding flowcharts  
- 📊 **Simulation results** — real-time measurement counts & histograms for the quantum protocol  
- 🎉 Success indicators (balloons, highlights) when decoding is correct  

---

## 🧠 What’s Inside?

### 🔮 Quantum (Superdense Coding)
1. **Entanglement creation** — Alice and Bob share a Bell pair.  
2. **Encoding (Alice)** — Applies X/Z gates based on the chosen 2-bit message.  
3. **Transmission** — Alice sends her qubit to Bob.  
4. **Decoding (Bob)** — Bob applies CNOT and H to recover the message.  
5. **Measurement** — Bob gets the exact 2-bit message.  

### 🔢 Classical (Repetition Code)
1. **Input** — 2-bit message to send.  
2. **Encoding** — Repeat bits for redundancy.  
3. **Transmission** — Send encoded bits.  
4. **Decoding** — Use parity checks to correct errors.  
5. **Output** — Reconstructed 2-bit message.  

---

## 🎛️ How to Use
- Pick a **2-bit message** (`00`, `01`, `10`, or `11`).  
- Step through **Quantum** and **Classical** sides independently with the **Next** buttons.  
- Observe:  
  - 🌀 Circuit diagrams evolve on the quantum side.  
  - 📊 Flowcharts evolve on the classical side.  
- At the end, compare decoded results and see the **efficiency gap**:  
  - **Quantum:** 2 bits sent with 1 qubit  
  - **Classical:** 2 bits require 2+ transmissions  

---

## 📦 Tech Stack
- [Streamlit](https://streamlit.io/) → Interactive app UI  
- [Qiskit](https://qiskit.org/) → Quantum circuit simulation  
- [Matplotlib](https://matplotlib.org/) → Measurement histograms  
- [NetworkX](https://networkx.org/) → Classical flowchart visualization  

---

## 🙌 Acknowledgements
- [Qiskit](https://qiskit.org/) — quantum computing framework  
- [Streamlit](https://streamlit.io/) — interactive web apps made easy  
- [NetworkX](https://networkx.org/) — graph-based visualizations  

---

## 📝 License
This project is released under the **MIT License**.  
Feel free to explore, learn, and build upon it.
