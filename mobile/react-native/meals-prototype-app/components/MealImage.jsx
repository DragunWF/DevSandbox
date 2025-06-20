import { StyleSheet, View, Image } from "react-native";

function MealImage({ source }) {
  return (
    <View style={styles.container}>
      <Image
        source={{
          uri: source,
        }}
        style={styles.image}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    justifyContent: "center",
    alignItems: "center",
  },
  image: {
    width: "90%",
    height: 350,
    resizeMode: "cover",
    borderRadius: 30,
    borderWidth: 3,
    borderColor: "black",
  },
});

export default MealImage;
