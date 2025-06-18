import { StyleSheet, View, Text, Modal, Button } from "react-native";
import RNExitApp from "react-native-exit-app";
import GameImage from "./GameImage";

function GameOverView({ isVisible, guessCount }) {
  function handleFinishGame() {
    RNExitApp.exitApp();
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
