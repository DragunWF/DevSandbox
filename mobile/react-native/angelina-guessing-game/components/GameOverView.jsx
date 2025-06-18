import {
  StyleSheet,
  View,
  Text,
  Modal,
  Button,
  DevSettings,
} from "react-native";
import GameImage from "./GameImage";

function GameOverView({ isVisible, guessCount }) {
  function handleFinishGame() {
    DevSettings.reload();
  }

  return (
    <Modal visible={isVisible} animationType="fade">
      <View style={styles.viewContainer}>
        <Text style={styles.textHeader}>Game Over!</Text>
        <GameImage source={require("../assets/images/game-over.png")} />
        <Text style={styles.textStat}>Guess Count: {guessCount}</Text>
        <View style={styles.finishButton}>
          <Button title="Finish" onPress={handleFinishGame} />
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  viewContainer: {
    backgroundColor: "#210F37",
    flex: 1,
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
  },
  textHeader: {
    color: "#fff",
    fontSize: 24,
  },
  textStat: {
    color: "#fff",
    marginTop: 10,
    fontSize: 18,
  },
  finishButton: {
    marginTop: 10,
  },
});

export default GameOverView;
