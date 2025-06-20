import { StyleSheet, View } from "react-native";

function Card({ children, style, backgroundColor }) {
  const cardBackgroundColor = backgroundColor ? backgroundColor : "#255F38";

  return (
    <View
      style={[
        { backgroundColor: cardBackgroundColor },
        styles.container,
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 20,
    paddingHorizontal: 50,
    borderRadius: 50,
    borderWidth: 5,
    borderColor: "#1a4629",
    elevation: 4,
    shadowColor: "black",
    shadowOffset: { width: 3, height: 3 },
    shadowRadius: 6,
    shadowOpacity: 0.5,
  },
});

export default Card;
