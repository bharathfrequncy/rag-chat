import { useState } from "react";

export default function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    setLoading(true);
    const res = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    setAnswer(data);
    setLoading(false);
  };

  const upload = async (e) => {
    const form = new FormData();
    form.append("file", e.target.files[0]);
    await fetch("http://localhost:8000/upload", { method: "POST", body: form });
    alert("File uploaded and indexed!");
  };

  return (
    <div style={{ maxWidth: 700, margin: "60px auto", fontFamily: "sans-serif" }}>
      <h1>Chat with your docs</h1>
      <input type="file" onChange={upload} accept=".pdf,.txt" />
      <div style={{ marginTop: 24 }}>
        <input
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Ask anything about your docs..."
          style={{ width: "80%", padding: 10, fontSize: 15 }}
          onKeyDown={e => e.key === "Enter" && ask()}
        />
        <button onClick={ask} style={{ padding: "10px 20px", marginLeft: 8 }}>
          Ask
        </button>
      </div>
      {loading && <p>Thinking...</p>}
      {answer && (
        <div style={{ marginTop: 24, padding: 20, background: "#f5f5f5", borderRadius: 8 }}>
          <p><strong>Answer:</strong> {answer.answer}</p>
          {answer.sources?.length > 0 && (
            <p style={{ fontSize: 13, color: "#666" }}>
              Sources: {answer.sources.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}