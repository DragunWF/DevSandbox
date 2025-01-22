import { useState } from "react";
import "./styles.css";

function App() {
  return (
    <div className="App">
      <Counter />
    </div>
  );
}

function Counter() {
  const [step, setStep] = useState(1);
  const [count, setCount] = useState(0);

  function getDaysCalculation() {
    if (count === 0) {
      return "Today is";
    } else if (count > 0) {
      return `${count} days from today is`;
    } else {
      return `${Math.abs(count)} days ago was`;
    }
  }

  function getDateCalculation() {
    const currentDate = new Date();
    currentDate.setDate(currentDate.getDate() + count);
    return currentDate.toDateString();
  }

  function reset() {
    setStep(1);
    setCount(0);
  }

  return (
    <div>
      <div>
        <input
          type="range"
          value={step}
          min="0"
          max="10"
          onChange={(e) => setStep(Number(e.target.value))}
        />
        {step}
      </div>
      <div>
        <button onClick={() => setCount((count) => count - step)}>-</button>
        <input
          type="number"
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
        />
        <button onClick={() => setCount((count) => count + step)}>+</button>
      </div>
      <p>
        {getDaysCalculation()} {getDateCalculation()}
      </p>
      {(count !== 0 || step !== 1) && (
        <input type="button" onClick={reset} value="Reset" />
      )}
    </div>
  );
}

export default App;
