import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

// Sample data
const skillList = [
  { name: "Python", level: "advanced", color: "#80DEEA" },
  { name: "JavaScript", level: "advanced", color: "#FFEB3B" },
  { name: "HTML", level: "intermediate", color: "#FF5722" },
  { name: "CSS", level: "intermediate", color: "#42A5F5" },
  { name: "React", level: "beginner", color: "#90CAF9" },
  { name: "Django", level: "beginner", color: "#FFC107" },
  { name: "Java", level: "intermediate", color: "#FF8A80" },
  { name: "C#", level: "intermediate", color: "#A5D6A7" },
  { name: "Unity", level: "beginner", color: "#FFD700" },
];

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
    <ul class="skill-list">
      {skillList.map((skill) => (
        <Skill skillObj={skill} />
      ))}
    </ul>
  );
}

function Skill({ skillObj }) {
  const emojiLevels = { beginner: "👶", intermediate: "👍", advanced: "💪" };
  const emoji = emojiLevels[skillObj.level];

  return (
    <li class="skill" style={{ backgroundColor: skillObj.color }}>
      {skillObj.name} {emoji}
    </li>
  );
}

const rootElement = document.getElementById("root");
const root = createRoot(rootElement);

root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
