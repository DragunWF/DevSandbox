import { useEffect, useState } from "react";

function App() {
  const [advice, setAdvice] = useState("<Advice will be displayed here>");
  const [buttonClickCount, updateClickCount] = useState(-1);

  async function getAdvice() {
    const res = await fetch("https://api.adviceslip.com/advice");
    const data = await res.json();

    setAdvice(data.slip.advice);
    updateClickCount((currentCount) => ++currentCount);
  }

  useEffect(function () {
    getAdvice();
  }, []);

  return (
    <div align="center">
      <h1>Welcome, Mr. IT Representative</h1>

      <Message buttonClickCount={buttonClickCount} advice={advice} />

      <button onClick={getAdvice}>Get Advice</button>
    </div>
  );
}

function Message(props) {
  return (
    <div>
      <p>"{props.advice}"</p>
      <p>
        <b>
          Times Clicked: <code>{props.buttonClickCount}</code>
        </b>
      </p>
    </div>
  );
}

export default App;
