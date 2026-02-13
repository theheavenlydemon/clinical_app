import { deleteSession, audioUrl, fetchHistory } from "../api";
import { useEffect, useState } from "react";

export default function HistoryPanel({ pid, refresh, onSelect }) {
  const [items, setItems] = useState([]);

  // reusable reload
  function reloadHistory() {
  fetchHistory(pid).then(setItems);
}

  // load on pid change or refresh trigger
  useEffect(() => {
    reloadHistory();
  }, [pid, refresh]);

  return (
    <div>
      {items.map((item) => (
        <div
          key={item.id}
          style={{
            background: "white",
            padding: 12,
            borderRadius: 8,
            marginBottom: 12,
            boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
            cursor: "pointer"
          }}
          onClick={() => onSelect(item)}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 8
            }}
          >
            <b>{item.patient_id}</b>

            <button
              onClick={(e) => {
                e.stopPropagation(); // prevent card click
                deleteSession(item.id);
                reloadHistory();
              }}
            >
              Delete
            </button>
          </div>

          <audio
            controls
            src={audioUrl(item.audio)}
            style={{ width: "100%", marginBottom: 8 }}
          />

          <h4>Transcript</h4>
          <p>{item.transcript}</p>

          <h4>Summary</h4>
          <p>{item.summary}</p>
        </div>
      ))}
    </div>
  );
}
