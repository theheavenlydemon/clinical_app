import { useState, useRef } from "react";
import { uploadAudio } from "../api";

export default function Recorder({ pid, onResult, onStatus }) {
  const [recording, setRecording] = useState(false);
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);

  async function start() {
    chunksRef.current = [];

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    streamRef.current = stream;

    const recorder = new MediaRecorder(stream, {
      mimeType: "audio/webm;codecs=opus"
    });

    recorderRef.current = recorder;

    recorder.ondataavailable = e => {
      if (e.data && e.data.size > 0) {
        chunksRef.current.push(e.data);
      }
    };

    recorder.start(1000); // <-- TIMESLICE (critical)
    setRecording(true);
    onStatus("Recording...");
  }

  async function stop() {
    const recorder = recorderRef.current;
    const stream = streamRef.current;

    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, {
        type: "audio/webm;codecs=opus"
      });

      console.log("Audio blob size:", blob.size);

      // stop mic hardware AFTER blob is created
      stream.getTracks().forEach(t => t.stop());

      if (blob.size < 10000) {
        onStatus("Mic captured no audio");
        return;
      }

      onStatus("Processing...");
      const res = await uploadAudio(blob, pid);
      onResult(res.id, res.transcript);
    };

    recorder.stop();
    setRecording(false);
  }

  return (
    <div>
      {!recording ? (
        <button style={btnStart} onClick={start}>
          🎤 Start Recording
        </button>
      ) : (
        <button style={btnStop} onClick={stop}>
          ⛔ Stop
        </button>
      )}
    </div>
  );
}

const btnStart = {
  background: "#2563eb",
  color: "#fff",
  padding: "12px 18px",
  borderRadius: 10,
  border: "none",
  cursor: "pointer"
};

const btnStop = {
  background: "#dc2626",
  color: "#fff",
  padding: "12px 18px",
  borderRadius: 10,
  border: "none",
  cursor: "pointer"
};
