class Player {
  constructor(name, health, stamina, experience) {
    this.name = name;
    this.health = health;
    this.stamina = stamina;
    this.experience = experience;
  }
}

const jewker = new Player("Jewker", 100, 50, 5);
const luq = new Player("Luq", 50, 100, 10);
const cpt = new Player("CPT", 25, 25, 50);
const players = [jewker, luq, cpt];

function switchPlayers(index) {
  const temp = players[index];
  players[index] = players[index + 1];
  players[index + 1] = temp;
}

function sortByAttribute(attributeName) {
  for (let i = 0; i < players.length; i++) {
    for (let j = 0; j < players.length - 1; j++) {
      switch (attributeName.toLowerCase()) {
        case "health":
          if (players[j].health > players[j + 1].health) switchPlayers(j);
          break;
        case "stamina":
          if (players[j].stamina > players[j + 1].stamina) switchPlayers(j);
          break;
        case "experience":
          if (players[j].experience > players[j + 1].experience)
            switchPlayers(j);
          break;
        default:
          throw new Error("Unknown attribute: " + attributeName);
      }
    }
  }
}

function getPlayerNames() {
  const names = [];
  for (let player of players) {
    names.push(player.name);
  }
  return `[${names.join(", ")}]`;
}

function displayPlayers(header) {
  console.log(`${header}: ${getPlayerNames()}`);
}

function main() {
  displayPlayers("Original");

  sortByAttribute("health");
  displayPlayers("Sort by health");

  sortByAttribute("stamina");
  displayPlayers("Sort by stamina");

  sortByAttribute("experience");
  displayPlayers("Sort by experience");
}

main();
