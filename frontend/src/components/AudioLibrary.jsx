import { useEffect, useState } from "react";
import { fetchAudioList } from "../api.js";

export default function AudioLibrary() {
  const [files, setFiles] = useState([]);

  useEffect(() => {
    fetchAudioList().then(setFiles);
  }, []);

  return (
    <div>
      <h4>Audio Library</h4>
      {files.map(f => (
        <div key={f.file} style={styles.row}>
          {f.file}
          <audio
            controls
            src={`http://127.0.0.1:8000/audio/${f.file}`}
          />
        </div>
      ))}
    </div>
  );
}

const styles = {
  row: {
    marginBottom: 10,
    fontSize: 13
  }
};
