import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function App() {
  return (
    <div className="card">
      <Avatar />
      <div className="data">
        <Intro />
        {/* Should contain one Skill component
        for each web dev skill that you have,
        customized with props */}
        <SkillList />
      </div>
    </div>
  );
}

function Avatar() {
  return <img className="avatar" src="./Avatar.jpg" alt="Avatar" />;
}

function Intro() {
  return (
    <div>
      <h1>Marc Plarisan</h1>
      <p>
        I'm am a 3rd-year IT Student at STI College Ortigas-Cainta who has been
        programming ever since I was a kid. I started with a game that involved
        scripting named Blocksworld. Eventually I transitioned to writing actual
        code when I got to Junior High School, the point of when I started to
        learn game development with the GoDot engine. Fast forward to today, I
        am now not only a game developer but also a competitive programmer, web
        developer, and mobile developer.
      </p>
    </div>
  );
}

function SkillList() {
  // I have more skills but I'll only list this for now...
  return (
    <div className="skill-list">
      <li className="skill" style={{ backgroundColor: "#80DEEA" }}>
        Python 💻
      </li>
      <li className="skill" style={{ backgroundColor: "#FFEB3B" }}>
        JavaScript 💻
      </li>
      <li className="skill" style={{ backgroundColor: "#FF5722" }}>
        HTML 💻
      </li>
      <li className="skill" style={{ backgroundColor: "#42A5F5" }}>
        CSS 💻
      </li>
      <li className="skill" style={{ backgroundColor: "#90CAF9" }}>
        React 💻
      </li>
      <li className="skill" style={{ backgroundColor: "#FFC107" }}>
        Django 💻
      </li>
      <li className="skill" style={{ backgroundColor: "#FF8A80" }}>
        Java 💻
      </li>
      <li className="skill" style={{ backgroundColor: "#A5D6A7" }}>
        C# 💻
      </li>
      <li className="skill" style={{ backgroundColor: "#FFD700" }}>
        Unity Game Engine 💻
      </li>
    </div>
  );
}

const rootElement = document.getElementById("root");
const root = createRoot(rootElement);

root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
