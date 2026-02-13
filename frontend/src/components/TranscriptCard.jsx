export default function TranscriptCard({transcript,summary}){

  function download(name,text){
    const blob = new Blob([text],{type:"text/plain"});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
  }

  return (
    <div>
      <p style={{
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
  overflowWrap: "break-word"
}}>
  {transcript}
</p>

      <button onClick={()=>download("transcript.txt",transcript)}>Export</button>
      

      <h4>Summary</h4>
      <p
  style={{
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    overflowWrap: "break-word",
    lineHeight: "1.5"
  }}
>
  {summary}
</p>

      <button onClick={()=>download("summary.txt",summary)}>Export</button>
    </div>
  );
}
