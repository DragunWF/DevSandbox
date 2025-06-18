import { StyleSheet, Image } from "react-native";

function GameImage({ source }) {
  return <Image style={styles.gameImage} source={source} />;
}

const styles = StyleSheet.create({
  gameImage: {
    width: 200,
    height: 200,
    marginTop: 20,
    marginBottom: 5,
    borderRadius: 15,
  },
});

export default GameImage;
