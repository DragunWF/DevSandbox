import { StatusBar } from "expo-status-bar";
import { StyleSheet, Text, View, Button } from "react-native";

export default function App() {
  return (
    <View style={styles.container}>
      <View>
        <Text style={styles.dummyText}>Another piece of text!</Text>
      </View>
      <View style={styles.card}>
        <Text style={styles.headerText}>Hallo World!</Text>
        <Text style={styles.descriptionText}>
          DragunWF now embarks on his quest to learn cross-platform mobile
          development. How exciting!
        </Text>
        <Button title="Click here for greatness" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
  },
  dummyText: {
    margin: 16,
    padding: 16,
    borderWidth: 2,
    borderColor: "blue",
  },
  card: {
    borderWidth: 1,
    borderColor: "black",
    padding: 10,
    margin: 10,
  },
  headerText: {
    fontSize: 50,
    textAlign: "center",
  },
  descriptionText: {
    fontSize: 24,
    textAlign: "center",
    margin: 20,
  },
});
