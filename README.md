# 🔮 Superdense Coding — Step-by-Step (Streamlit App)

This project is an **interactive simulator** for learning **Superdense Coding** using [Qiskit](https://qiskit.org/) and [Streamlit](https://streamlit.io/).  
It reveals each step of the protocol interactively, helping you understand how **two classical bits** can be transmitted using only **one qubit** and shared entanglement.

👉 **Live Demo:** [Quantum Superdense Coding App](https://quantum-superdense-coding.streamlit.app/)

---

## ✨ Features
- 🚀 **Interactive step-by-step exploration** — progress through each stage with a button  
- 🌀 **Smooth transitions** to make the learning experience more engaging  
- 🔎 **Compact circuit diagrams** so the circuits fit neatly on the screen  
- 📊 **Real-time simulation results** — see measurement counts and histograms  
- ✅ Runs directly in the browser on Streamlit Cloud (no setup required)

---

## 🧠 What is Superdense Coding?
Superdense coding is a **quantum communication protocol** that demonstrates the power of entanglement.  

It allows **two classical bits** of information to be communicated by sending only **one qubit**, provided that Alice and Bob already share an entangled pair of qubits.  

### Protocol Overview
1. **Entanglement Creation**  
   Alice and Bob share a Bell pair (|Φ+⟩).  

2. **Encoding (Alice’s step)**  
   - Depending on the 2-bit message (`00`, `01`, `10`, or `11`), Alice applies a combination of **X** and **Z** gates to her qubit.  
   - These gates encode her classical information into the quantum state.  

3. **Transmission**  
   Alice sends her qubit to Bob (only one qubit is transmitted).  

4. **Decoding (Bob’s step)**  
   Bob applies a **CNOT** and a **Hadamard** gate to decode the state.  

5. **Measurement**  
   Measuring the two qubits gives Bob the exact **2-bit classical message** Alice wanted to send.  

---

## 🎛️ How to Use the App
- Select the **2-bit message** you want Alice to send (`00`, `01`, `10`, or `11`).  
- Click **Next** to reveal each stage of the protocol:  
  - Entanglement → Encoding → Transmission → Decoding → Measurement.  
- At the end, you’ll see:  
  - ✅ The decoded message (what Bob receives)  
  - 📊 Measurement statistics (histogram and counts)  

---

## 📦 Tech Stack
- [Streamlit](https://streamlit.io/) → Interactive UI  
- [Qiskit](https://qiskit.org/) → Quantum simulation & circuits  
- [Matplotlib](https://matplotlib.org/) → Visualization of measurement results  

---

## 🙌 Acknowledgements
- [Qiskit](https://qiskit.org/) — for providing the quantum computing framework  
- [Streamlit](https://streamlit.io/) — for making interactive demos simple and accessible  

---

## 📝 License
This project is released under the **MIT License**.  
Feel free to learn, share, and build upon it.
