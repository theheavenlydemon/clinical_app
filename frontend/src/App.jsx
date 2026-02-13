import { useState, useEffect } from "react";
import { fetchHistory } from "./api";
import Recorder from "./components/Recorder";
import TranscriptCard from "./components/TranscriptCard";
import HistoryPanel from "./components/HistoryPanel";

export default function App() {

  const [token, setToken] = useState(localStorage.getItem("token"));

  const [tab, setTab] = useState("main");
  const [transcript, setTranscript] = useState("");
  const [summary, setSummary] = useState("");
  const [status, setStatus] = useState("Idle");
  const [patientId, setPatientId] = useState("P001");
  const [searchId, setSearchId] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [miniHistory, setMiniHistory] = useState([]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);


  useEffect(() => {
  fetchHistory(searchId).then(setMiniHistory);
}, [searchId, refresh]);

  async function handleResult(id, transcript) {
  setTranscript(transcript);
  setSummary("");               // start empty

  const interval = setInterval(async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/summary/${id}`);
      const data = await res.json();

      // IMPORTANT: only stop when summary is a STRING
      if (data.summary && data.summary !== "Summarizing...") {
  setSummary(data.summary);
  setStatus("Completed");
  clearInterval(interval);
}

    } catch (e) {
      console.error("Summary fetch failed", e);
      clearInterval(interval);
      setStatus("Summary failed");
    }
  }, 2000);
}


  function loadHistory(item) {
    setTranscript(item.transcript);
    setSummary(item.summary);
    setStatus("Loaded from history");
  }

if (!token) {
  return (
    <div style={styles.authContainer}>
      <div style={styles.authBox}>
        <h2>{isRegister ? "Create Account" : "Doctor Login"}</h2>

        <input
          style={styles.input}
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          style={styles.input}
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          style={styles.primaryBtn}
          onClick={async () => {
            const form = new FormData();

           if (isRegister) {
  const form = new FormData();
  form.append("email", email);
  form.append("password", password);

  try {
    const res = await fetch("http://127.0.0.1:8000/register", {
      method: "POST",
      body: form,
    });

    const data = await res.json();
    console.log("Register response:", data);

    if (res.ok) {
      alert("Account created successfully!");
      setIsRegister(false);
    } else {
      alert(data.detail || "Registration failed");
    }

  } catch (err) {
    console.error("Register error:", err);
    alert("Server not responding");
  }
}
 else {
              form.append("username", email);
              form.append("password", password);

              const res = await fetch("http://127.0.0.1:8000/login", {
                method: "POST",
                body: form,
              });

              const data = await res.json();

              if (res.ok) {
                localStorage.setItem("token", data.access_token);
                setToken(data.access_token);
              } else {
                alert(data.detail || "Login failed");
              }
            }
          }}
        >
          {isRegister ? "Register" : "Login"}
        </button>

        <p
          style={{ marginTop: 15, cursor: "pointer", color: "#2563eb" }}
          onClick={() => setIsRegister(!isRegister)}
        >
          {isRegister
            ? "Already have an account? Login"
            : "Don't have an account? Register"}
        </p>
      </div>
    </div>
  );
}

return (
  <div style={styles.app}>

    <aside style={styles.sidebar}>
      <h3>Clinical Dictation</h3>

      <button onClick={()=>setTab("main")} style={styles.navBtn}>
        Main
      </button>

      <button onClick={()=>setTab("db")} style={styles.navBtn}>
        Database
      </button>

      <button
        style={styles.logoutBtn}
        onClick={() => {
          localStorage.removeItem("token");
          setToken(null);
        }}
      >
        Logout
      </button>

      <hr style={{margin:"12px 0"}}/>

      <div style={{marginBottom:12}}>
        <label>Assign Patient ID</label>
        <input
          style={{width:"100%",marginTop:4}}
          value={patientId}
          onChange={e=>setPatientId(e.target.value)}
        />
      </div>

      <div>
        <label>Search Sessions</label>
        <input
          style={{width:"100%",marginTop:4}}
          value={searchId}
          onChange={e=>setSearchId(e.target.value)}
        />
      </div>

      <div style={{
        marginTop:10,
        maxHeight:160,
        overflowY:"auto"
      }}>
        {miniHistory.map(item => (
          <div
            key={item.id}
            onClick={() => loadHistory(item)}
            style={{
              padding:6,
              marginBottom:4,
              background:"#2a3550",
              borderRadius:6,
              cursor:"pointer",
              fontSize:13
            }}
          >
            {item.patient_id} – {item.transcript.slice(0,20)}...
          </div>
        ))}
      </div>

    </aside>

    {/* 🔥 RESTORED MAIN SECTION */}
    <main style={styles.main}>

      {tab==="main" && (
        <>
          <div style={styles.card}>
            <Recorder
              pid={patientId}
              onResult={handleResult}
              onStatus={setStatus}
            />
          </div>

          {(transcript || summary) && (
            <div style={styles.card}>
              <TranscriptCard
                transcript={transcript}
                summary={summary}
              />
            </div>
          )}
        </>
      )}

      {tab==="db" && (
        <div style={styles.card}>
          <h3>Session Database</h3>
          <HistoryPanel
            pid={searchId}
            refresh={refresh}
            onSelect={loadHistory}
          />
        </div>
      )}

    </main>

  </div>
);
}

const styles = {
  app: {
    display: "flex",
    fontFamily: "Arial, sans-serif",
    height: "100vh",
    background: "#f3f4f6"
  },

  sidebar: {
    width: 260,
    background: "#0f172a",
    color: "white",
    padding: 16,
    overflowY: "auto"
  },

  main: {
    flex: 1,
    padding: 24,
    overflowY: "auto"
  },

  card: {
    background: "white",
    padding: 20,
    borderRadius: 10,
    boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
    marginBottom: 20
  },

  navBtn: {
    width: "100%",
    padding: 10,
    marginBottom: 8,
    background: "#1e293b",
    color: "white",
    border: "none",
    borderRadius: 6,
    cursor: "pointer"
  },

  input: {
    width: "100%",
    padding: 10,
    borderRadius: 6,
    border: "1px solid #ccc",
    marginBottom: 10
  },

  authContainer: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    background: "#f3f4f6"
  },

  authBox: {
    width: 350,
    padding: 30,
    background: "white",
    borderRadius: 12,
    boxShadow: "0 6px 18px rgba(0,0,0,0.15)",
    textAlign: "center"
  },

  primaryBtn: {
    width: "100%",
    padding: 10,
    marginTop: 12,
    background: "#2563eb",
    color: "white",
    border: "none",
    borderRadius: 6,
    cursor: "pointer"
  },

  logoutBtn: {
    width: "100%",
    padding: 10,
    marginTop: 12,
    background: "#ef4444",
    color: "white",
    border: "none",
    borderRadius: 6,
    cursor: "pointer"
  }
};
