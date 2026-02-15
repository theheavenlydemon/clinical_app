import { Routes, Route } from "react-router-dom";
import Reset from "./Reset";
import { useState, useEffect } from "react";
import { fetchHistory, fetchAudit } from "./api";
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
  const [auditLogs, setAuditLogs] = useState([]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [isForgot, setIsForgot] = useState(false);
  const [resetPassword, setResetPassword] = useState("");




  useEffect(() => {
  fetchHistory(searchId).then(setMiniHistory);
}, [searchId, refresh]);

useEffect(() => {
  if (tab === "audit") {
    fetch("http://127.0.0.1:8000/audit", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    .then(res => res.json())
    .then(data => setAuditLogs(data))
    .catch(err => {
      console.error(err);
      alert("Failed to load audit logs");
    });
  }
}, [tab, token]);



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

async function handleAuth() {
  const form = new FormData();

  if (isForgot) {
  const form = new FormData();
  form.append("email", email);

  const res = await fetch("http://127.0.0.1:8000/forgot-password", {
    method: "POST",
    body: form,
  });

  const data = await res.json();
  alert(data.status);
  setIsForgot(false);
  return;
}

  if (isRegister) {

    form.append("email", email);
    form.append("password", password);

    const res = await fetch("http://127.0.0.1:8000/register", {
      method: "POST",
      body: form,
    });

    let data = null;

    try {
      data = await res.json();
    } catch (err) {
      console.log("No JSON returned from register");
    }

    console.log("Register response:", data);

    if (res.ok) {
      alert("Registered successfully! Check console for verification link.");
      console.log("Verification link:", data?.verification_link);
      setIsRegister(false);
    } else {
      alert(data?.detail || "Registration failed");
    }

  } else {

const res = await fetch("http://127.0.0.1:8000/login", {
  method: "POST",
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
  },
  body: new URLSearchParams({
    username: email,
    password: password,
  }),
});


    let data = null;

    try {
      data = await res.json();
    } catch (err) {
      console.log("No JSON returned from login");
    }

    console.log("Login response:", data);

    if (res.ok && data && data.access_token) {
      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
    } else {
      alert(data?.detail || "Login failed");
    }
  }
}


if (!token) {
  return (
    <div style={styles.authContainer}>
      <div style={styles.authCard}>

        <div style={styles.authHeader}>
          <h2>{isRegister ? "Create Account" : "Welcome Back"}</h2>
          <p style={{color:"#6b7280"}}>
            {isRegister
              ? "Register to access the clinical system"
              : "Login to access clinical dictation"}
          </p>
        </div>

        <input
          style={styles.authInput}
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          style={styles.authInput}
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {!isRegister && !isForgot && (
  <div
    style={{ textAlign: "right", fontSize: 13, cursor: "pointer", color:"#2563eb" }}
    onClick={() => setIsForgot(true)}
  >
    Forgot Password?
  </div>
)}


        <button
          style={styles.authButton}
          onClick={handleAuth}
        >
          {isRegister ? "Create Account" : "Login"}
        </button>

        <div style={styles.authSwitch}>
          {isRegister ? "Already registered?" : "New here?"}
          <span
            style={styles.switchLink}
            onClick={() => setIsRegister(!isRegister)}
          >
            {isRegister ? " Login" : " Create Account"}
          </span>
        </div>

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

      <button onClick={()=>setTab("audit")} style={styles.navBtn}>
  Audit Logs
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

      {tab==="audit" && (
  <div style={styles.card}>
    <h3>Audit Logs</h3>

    {auditLogs.length === 0 ? (
      <p>No audit logs yet.</p>
    ) : (
      <div style={{maxHeight:400, overflowY:"auto"}}>
        {auditLogs.map(log => (
          <div
            key={log[0]}
            style={{
              padding:10,
              borderBottom:"1px solid #eee",
              fontSize:13
            }}
          >
            <strong>User:</strong> {log[1]} <br/>
            <strong>Action:</strong> {log[2]} <br/>
            <strong>Patient:</strong> {log[3] || "-"} <br/>
            <strong>Session:</strong> {log[4] || "-"} <br/>
            <strong>Time:</strong> {new Date(log[5]*1000).toLocaleString()}
          </div>
        ))}
      </div>
    )}
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
  },
  
  authContainer: {
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  height: "100vh",
  background: "linear-gradient(135deg,#0f172a,#1e293b)"
},

authCard: {
  width: 380,
  background: "white",
  padding: 35,
  borderRadius: 16,
  boxShadow: "0 15px 35px rgba(0,0,0,0.25)"
},

authHeader: {
  marginBottom: 25
},

authInput: {
  width: "100%",
  padding: 12,
  marginBottom: 15,
  borderRadius: 8,
  border: "1px solid #e5e7eb",
  fontSize: 14
},

authButton: {
  width: "100%",
  padding: 12,
  background: "#2563eb",
  color: "white",
  border: "none",
  borderRadius: 8,
  fontWeight: "600",
  cursor: "pointer",
  marginBottom: 15
},

authSwitch: {
  textAlign: "center",
  fontSize: 14
},

switchLink: {
  color: "#2563eb",
  cursor: "pointer",
  marginLeft: 5,
  fontWeight: "600"
},

};
