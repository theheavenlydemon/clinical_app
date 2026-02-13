const BASE = "http://127.0.0.1:8000";
function authHeader(){
  return {
    Authorization: `Bearer ${localStorage.getItem("token")}`
  };
}


// ---------- UPLOAD AUDIO ----------

export async function uploadAudio(blob, pid) {
  const fd = new FormData();
  fd.append("audio", blob);
  fd.append("patient_id", pid);

  const r = await fetch(`${BASE}/transcribe`, {
  method: "POST",
  body: fd,
  headers: authHeader()
});


  if (!r.ok) throw new Error("Upload failed");
  return r.json();
}

// ---------- FETCH HISTORY ----------

export async function fetchHistory(pid) {
  const r = await fetch(`${BASE}/history/${pid}`,{
  headers: authHeader()
});

  if (!r.ok) return [];
  return r.json();
}

// ---------- DELETE SESSION ----------

export async function deleteSession(id) {
  await fetch(`${BASE}/session/${id}`, {
  method: "DELETE",
  headers: authHeader()
});
}

// ---------- AUDIO URL ----------

export function audioUrl(path) {
  if (!path) return "";
  const file = path.split("/").pop();
  return `${BASE}/audio/${file}`;
}

export async function fetchAllHistory() {
  const r = await fetch(`${BASE}/history`,{
  headers: authHeader()
});

  return r.json();
}
