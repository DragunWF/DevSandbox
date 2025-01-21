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

  return (
    <div>
      <div>
        <button onClick={() => setStep((step) => --step)}>-</button>
        <span>Step: {step}</span>
        <button onClick={() => setStep((step) => ++step)}>+</button>
      </div>
      <div>
        <button onClick={() => setCount((count) => count - step)}>-</button>
        <span>Count: {count}</span>
        <button onClick={() => setCount((count) => count + step)}>+</button>
      </div>
      <p>
        {getDaysCalculation()} {getDateCalculation()}
      </p>
    </div>
  );
}

export default App;
