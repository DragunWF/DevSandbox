import { StyleSheet, View, Text, Modal } from "react-native";
import GameImage from "./GameImage";

function GameOverView({ isVisible, guessCount }) {
  return (
    <Modal visible={isVisible} animationType="fade">
      <View style={styles.viewContainer}>
        <Text style={styles.textHeader}>Game Over!</Text>
        <GameImage source={"../assets/images/game-over.png"} />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  viewContainer: {
    backgroundColor: "#210F37",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
  },
  textHeader: {
    color: "#fff",
    fontSize: 24,
  },
});

export default GameOverView;
