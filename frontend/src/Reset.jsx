import { useState } from "react";
import { useParams } from "react-router-dom";

export default function Reset() {
  const { token } = useParams();
  const [password, setPassword] = useState("");

  async function handleReset() {
    const form = new FormData();
    form.append("new_password", password);

    const res = await fetch(`http://127.0.0.1:8000/reset-password/${token}`, {
      method: "POST",
      body: form,
    });

    const data = await res.json();
    alert(data.status || data.detail);
  }

  return (
    <div style={{padding:40}}>
      <h2>Set New Password</h2>
      <input
        type="password"
        placeholder="New Password"
        value={password}
        onChange={(e)=>setPassword(e.target.value)}
      />
      <button onClick={handleReset}>Reset Password</button>
    </div>
  );
}
