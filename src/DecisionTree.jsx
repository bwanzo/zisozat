import { useState } from "react";

const ROUNDS = 3;

const systemPrompt = `You are a decision tree facilitator. Your job is to meet users where they are in their decision-making process and help them explore the actual decision space.

CRITICAL - Read the user's question carefully:
- If they ask "Should I..." or "Do I..." → They haven't decided yet. Explore WHETHER, not HOW.
- If they ask "How do I..." → They've decided. Explore approach/method.

For Round 1 (initial question):
- DON'T assume they've decided to do it
- DON'T jump to logistics or implementation ("fly vs drive", "email vs call")  
- DO explore the actual decision ("prioritize stability vs growth", "stay or go")
- DO present different underlying motivations or considerations

For Rounds 2-3:
- Follow the path they've chosen
- Get progressively more specific
- By Round 3, options can be concrete next actions

Rules:
- Options should be under 10 words
- Options must be meaningfully different (not just yes/no)
- Stay coherent with the user's chosen path
- Never assume a decision that hasn't been made

Respond ONLY with a JSON object, no markdown, no explanation:
{
  "optionA": "...",
  "optionB": "..."
}`;

const outcomePrompt = `You are a thoughtful advisor. Given a user's initial question and the path they chose, write a reflective insight about their decision journey.

Your insight should:
- Acknowledge what their choices reveal about their priorities or values
- Offer perspective on the path they've taken
- Be 2-4 sentences, warm and thoughtful (not robotic)
- Avoid being prescriptive - reflect, don't command

Respond ONLY with a JSON object:
{
  "outcome": "..."
}`;

async function fetchOptions(question, path, feedback = null) {
  const pathText = path.length > 0
    ? `\n\nChoices made so far:\n${path.map((p, i) => `Round ${i + 1}: "${p}"`).join("\n")}`
    : "";
  const round = path.length + 1;
  
  const feedbackText = feedback
    ? `\n\nUser feedback on previous options: ${feedback}\nPlease generate completely different options that address this feedback.`
    : "";

  const response = await fetch("/api/anthropic", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system: systemPrompt,
      messages: [{
        role: "user",
        content: `Initial question: "${question}"${pathText}${feedbackText}\n\nNow generate 2 options for Round ${round}.`
      }]
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to fetch options');
  }

  const data = await response.json();
  const text = data.content?.find(b => b.type === "text")?.text || "{}";
  return JSON.parse(text.replace(/```json|```/g, "").trim());
}

async function fetchOutcome(question, path) {
  const response = await fetch("/api/anthropic", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system: outcomePrompt,
      messages: [{
        role: "user",
        content: `Initial question: "${question}"\n\nDecisions made:\n${path.map((p, i) => `Round ${i + 1}: "${p}"`).join("\n")}`
      }]
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to fetch outcome');
  }

  const data = await response.json();
  const text = data.content?.find(b => b.type === "text")?.text || "{}";
  const parsed = JSON.parse(text.replace(/```json|```/g, "").trim());
  return parsed.outcome;
}

function Breadcrumb({ question, path }) {
  if (path.length === 0) return null;

  return (
    <div style={{
      display: "flex",
      flexWrap: "wrap",
      alignItems: "center",
      gap: "6px",
      marginBottom: "36px",
      padding: "14px 18px",
      background: "#f8f8f6",
      borderRadius: "10px",
      border: "1px solid #ececea"
    }}>
      <span style={{ fontSize: "12px", color: "#999", fontFamily: "'DM Mono', monospace", letterSpacing: "0.05em" }}>PATH</span>
      <span style={{ color: "#ccc", fontSize: "12px" }}>—</span>
      <span style={{ fontSize: "13px", color: "#555", fontStyle: "italic" }}>{question}</span>
      {path.map((choice, i) => (
        <span key={i} style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ color: "#d0d0ce", fontSize: "14px" }}>›</span>
          <span style={{
            fontSize: "13px",
            color: "#1a1a1a",
            fontWeight: "500",
            background: "#fff",
            padding: "2px 10px",
            borderRadius: "20px",
            border: "1px solid #e0e0dd"
          }}>{choice}</span>
        </span>
      ))}
    </div>
  );
}

function ChoiceButton({ label, onClick, disabled }) {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: "100%",
        padding: "20px 24px",
        background: hovered ? "#1a1a1a" : "#fff",
        color: hovered ? "#fff" : "#1a1a1a",
        border: "1.5px solid",
        borderColor: hovered ? "#1a1a1a" : "#ddddd9",
        borderRadius: "12px",
        fontSize: "15px",
        fontFamily: "'Lora', Georgia, serif",
        fontWeight: "400",
        cursor: disabled ? "default" : "pointer",
        textAlign: "left",
        lineHeight: "1.4",
        transition: "all 0.18s ease",
        opacity: disabled ? 0.5 : 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px"
      }}
    >
      <span>{label}</span>
      <span style={{ opacity: hovered ? 1 : 0.3, fontSize: "18px", transition: "opacity 0.18s ease" }}>→</span>
    </button>
  );
}

function RoundDots({ current, total }) {
  return (
    <div style={{ display: "flex", gap: "8px", justifyContent: "center", marginBottom: "32px" }}>
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} style={{
          width: i < current ? "24px" : "8px",
          height: "8px",
          borderRadius: "4px",
          background: i < current ? "#1a1a1a" : (i === current ? "#999" : "#ddd"),
          transition: "all 0.3s ease"
        }} />
      ))}
    </div>
  );
}

export default function DecisionTree() {
  const [question, setQuestion] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [path, setPath] = useState([]);
  const [options, setOptions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [outcome, setOutcome] = useState(null);
  const [phase, setPhase] = useState("input"); // input | choosing | done
  const [error, setError] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState("");

  const round = path.length; // 0-indexed current round

  async function startTree() {
    if (!inputValue.trim()) return;

    setLoading(true);
    setError(null);
    setQuestion(inputValue.trim());
    setPath([]);
    setPhase("choosing");
    setShowFeedback(false);

    try {
      const opts = await fetchOptions(inputValue.trim(), []);
      setOptions(opts);
    } catch (e) {
      setError(e.message || "Something went wrong. Please try again.");
      setPhase("input");
    }

    setLoading(false);
  }

  async function refreshOptions() {
    if (!selectedFeedback) {
      setError("Please select a reason for new options.");
      return;
    }

    setLoading(true);
    setError(null);
    setShowFeedback(false);
    setOptions(null);

    try {
      const opts = await fetchOptions(question, path, selectedFeedback);
      setOptions(opts);
      setSelectedFeedback("");
    } catch (e) {
      setError(e.message || "Couldn't load new options. Please try again.");
    }

    setLoading(false);
  }

  async function choose(option) {
    const newPath = [...path, option];
    setPath(newPath);

    if (newPath.length >= ROUNDS) {
      setLoading(true);
      setOptions(null);

      try {
        const result = await fetchOutcome(question, newPath);
        setOutcome(result);
        setPhase("done");
      } catch (e) {
        setError(e.message || "Couldn't generate outcome. Please try again.");
      }

      setLoading(false);
    } else {
      setLoading(true);
      setOptions(null);

      try {
        const opts = await fetchOptions(question, newPath);
        setOptions(opts);
      } catch (e) {
        setError(e.message || "Couldn't load next options. Please try again.");
      }

      setLoading(false);
    }
  }

  function reset() {
    setPhase("input");
    setInputValue("");
    setQuestion("");
    setPath([]);
    setOptions(null);
    setOutcome(null);
    setError(null);
    setShowFeedback(false);
    setSelectedFeedback("");
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "#fafaf8",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "40px 20px",
      fontFamily: "'Lora', Georgia, serif"
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;1,400&family=DM+Mono:wght@300;400;500&display=swap');
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::placeholder { color: #bbb; }
        textarea:focus { outline: none; }
        button:focus { outline: none; }
        
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .fade-up { animation: fadeUp 0.4s ease forwards; }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .spinner {
          width: 20px; height: 20px;
          border: 2px solid #ddd;
          border-top-color: #1a1a1a;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          margin: 0 auto;
        }
      `}</style>

      <div style={{ width: "100%", maxWidth: "560px" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "48px" }}>
          <div style={{
            fontSize: "11px",
            letterSpacing: "0.15em",
            color: "#aaa",
            fontFamily: "'DM Mono', monospace",
            marginBottom: "12px",
            textTransform: "uppercase"
          }}>Decision Tree</div>
          <h1 style={{
            fontSize: "28px",
            fontWeight: "400",
            color: "#1a1a1a",
            lineHeight: "1.3",
            fontStyle: "italic"
          }}>What are you deciding?</h1>
        </div>

        {/* Input Phase */}
        {phase === "input" && (
          <div className="fade-up">
            <textarea
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); startTree(); } }}
              placeholder="e.g. Should I quit my job? Should I move to a new city?"
              rows={3}
              style={{
                width: "100%",
                padding: "18px 20px",
                fontSize: "15px",
                fontFamily: "'Lora', Georgia, serif",
                border: "1.5px solid #ddddd9",
                borderRadius: "12px",
                background: "#fff",
                color: "#1a1a1a",
                resize: "none",
                lineHeight: "1.5",
                marginBottom: "14px"
              }}
            />
            <button
              onClick={startTree}
              disabled={!inputValue.trim() || loading}
              style={{
                width: "100%",
                padding: "16px",
                background: inputValue.trim() ? "#1a1a1a" : "#e8e8e5",
                color: inputValue.trim() ? "#fff" : "#aaa",
                border: "none",
                borderRadius: "12px",
                fontSize: "14px",
                fontFamily: "'DM Mono', monospace",
                letterSpacing: "0.05em",
                cursor: inputValue.trim() ? "pointer" : "default",
                transition: "all 0.2s ease"
              }}
            >
              {loading ? <div className="spinner" /> : "Begin →"}
            </button>
            {error && <p style={{ color: "#c0392b", fontSize: "13px", marginTop: "12px", textAlign: "center" }}>{error}</p>}
          </div>
        )}

        {/* Choosing Phase */}
        {phase === "choosing" && (
          <div className="fade-up">
            <Breadcrumb question={question} path={path} />
            <RoundDots current={round} total={ROUNDS} />
            
            <p style={{
              fontSize: "12px",
              fontFamily: "'DM Mono', monospace",
              color: "#aaa",
              letterSpacing: "0.08em",
              textAlign: "center",
              marginBottom: "20px"
            }}>ROUND {round + 1} OF {ROUNDS}</p>

            <p style={{
              fontSize: "17px",
              color: "#1a1a1a",
              lineHeight: "1.5",
              marginBottom: "24px",
              textAlign: "center",
              fontStyle: round === 0 ? "italic" : "normal"
            }}>
              {round === 0 ? `"${question}"` : `You chose: "${path[path.length - 1]}"`}
            </p>

            {loading ? (
              <div style={{ padding: "40px", textAlign: "center" }}>
                <div className="spinner" />
                <p style={{ color: "#bbb", fontSize: "13px", marginTop: "14px", fontFamily: "'DM Mono', monospace" }}>
                  thinking...
                </p>
              </div>
            ) : options ? (
              <>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }} className="fade-up">
                  <ChoiceButton label={options.optionA} onClick={() => choose(options.optionA)} disabled={false} />
                  <div style={{ textAlign: "center", color: "#ccc", fontSize: "12px", fontFamily: "'DM Mono', monospace", padding: "8px 0" }}>or</div>
                  <ChoiceButton label={options.optionB} onClick={() => choose(options.optionB)} disabled={false} />
                </div>

                {!showFeedback ? (
                  <button
                    onClick={() => setShowFeedback(true)}
                    style={{
                      marginTop: "20px",
                      padding: "10px 16px",
                      background: "transparent",
                      color: "#999",
                      border: "1px solid #e0e0dd",
                      borderRadius: "8px",
                      fontSize: "12px",
                      fontFamily: "'DM Mono', monospace",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      width: "100%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "6px"
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.borderColor = "#1a1a1a";
                      e.target.style.color = "#1a1a1a";
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.borderColor = "#e0e0dd";
                      e.target.style.color = "#999";
                    }}
                  >
                    <span style={{ fontSize: "14px" }}>↻</span>
                    <span>Don't like these? Get different options</span>
                  </button>
                ) : (
                  <div className="fade-up" style={{
                    marginTop: "20px",
                    padding: "18px",
                    background: "#f8f8f6",
                    borderRadius: "10px",
                    border: "1px solid #ececea"
                  }}>
                    <p style={{
                      fontSize: "13px",
                      fontFamily: "'DM Mono', monospace",
                      color: "#666",
                      marginBottom: "14px",
                      letterSpacing: "0.02em"
                    }}>Why do you want different options?</p>
                    
                    {[
                      { value: "Both options are too similar", label: "Both options are too similar" },
                      { value: "Options don't address my concern", label: "Options don't address my concern" },
                      { value: "I need more creative alternatives", label: "I need more creative alternatives" },
                      { value: "These are too extreme or dramatic", label: "These are too extreme/dramatic" },
                      { value: "I need more practical options", label: "I need more practical options" }
                    ].map((option) => (
                      <label
                        key={option.value}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          padding: "10px 12px",
                          marginBottom: "8px",
                          background: selectedFeedback === option.value ? "#fff" : "transparent",
                          borderRadius: "6px",
                          cursor: "pointer",
                          transition: "background 0.15s ease",
                          fontSize: "13px",
                          fontFamily: "'Lora', Georgia, serif",
                          color: "#1a1a1a"
                        }}
                        onMouseEnter={(e) => {
                          if (selectedFeedback !== option.value) {
                            e.currentTarget.style.background = "#fff";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (selectedFeedback !== option.value) {
                            e.currentTarget.style.background = "transparent";
                          }
                        }}
                      >
                        <input
                          type="radio"
                          name="feedback"
                          value={option.value}
                          checked={selectedFeedback === option.value}
                          onChange={(e) => setSelectedFeedback(e.target.value)}
                          style={{ accentColor: "#1a1a1a", cursor: "pointer" }}
                        />
                        <span>{option.label}</span>
                      </label>
                    ))}

                    <div style={{ display: "flex", gap: "8px", marginTop: "14px" }}>
                      <button
                        onClick={() => {
                          setShowFeedback(false);
                          setSelectedFeedback("");
                          setError(null);
                        }}
                        style={{
                          flex: "1",
                          padding: "10px",
                          background: "#fff",
                          color: "#666",
                          border: "1px solid #ddd",
                          borderRadius: "6px",
                          fontSize: "12px",
                          fontFamily: "'DM Mono', monospace",
                          cursor: "pointer"
                        }}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={refreshOptions}
                        disabled={!selectedFeedback || loading}
                        style={{
                          flex: "2",
                          padding: "10px",
                          background: selectedFeedback ? "#1a1a1a" : "#e8e8e5",
                          color: selectedFeedback ? "#fff" : "#aaa",
                          border: "none",
                          borderRadius: "6px",
                          fontSize: "12px",
                          fontFamily: "'DM Mono', monospace",
                          cursor: selectedFeedback ? "pointer" : "default",
                          letterSpacing: "0.05em"
                        }}
                      >
                        Generate New Options
                      </button>
                    </div>
                  </div>
                )}

                {error && <p style={{ color: "#c0392b", fontSize: "12px", marginTop: "12px", textAlign: "center" }}>{error}</p>}
              </>
            ) : null}
          </div>
        )}

        {/* Done Phase */}
        {phase === "done" && (
          <div className="fade-up">
            <Breadcrumb question={question} path={path} />
            
            <div style={{
              background: "#fff",
              border: "1.5px solid #ddddd9",
              borderRadius: "16px",
              padding: "32px 28px",
              marginBottom: "24px"
            }}>
              <div style={{
                fontSize: "11px",
                letterSpacing: "0.12em",
                color: "#aaa",
                fontFamily: "'DM Mono', monospace",
                marginBottom: "16px",
                textTransform: "uppercase"
              }}>Where this path leads</div>

              {loading ? (
                <div style={{ padding: "20px 0", textAlign: "center" }}>
                  <div className="spinner" />
                </div>
              ) : (
                <p style={{
                  fontSize: "16px",
                  color: "#2a2a2a",
                  lineHeight: "1.7",
                  fontStyle: "italic"
                }}>{outcome}</p>
              )}
            </div>

            <button
              onClick={reset}
              style={{
                width: "100%",
                padding: "16px",
                background: "transparent",
                color: "#1a1a1a",
                border: "1.5px solid #ddddd9",
                borderRadius: "12px",
                fontSize: "14px",
                fontFamily: "'DM Mono', monospace",
                letterSpacing: "0.05em",
                cursor: "pointer",
                transition: "all 0.2s ease"
              }}
              onMouseEnter={e => { e.target.style.background = "#1a1a1a"; e.target.style.color = "#fff"; }}
              onMouseLeave={e => { e.target.style.background = "transparent"; e.target.style.color = "#1a1a1a"; }}
            >
              Start a new decision →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
