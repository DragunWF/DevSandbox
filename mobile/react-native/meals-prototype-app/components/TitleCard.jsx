import { StyleSheet, View } from "react-native";
import Card from "./Card";
import Title from "./Title";

function TitleCard({ children }) {
  return (
    <View style={styles.headContainer}>
      <Card style={styles.titleCardContainer}>
        <Title>{children}</Title>
      </Card>
    </View>
  );
}

const styles = StyleSheet.create({
  headContainer: {
    width: "100%",
    padding: 15,
  },
  categoriesContainer: {
    marginTop: 10,
  },
  titleCardContainer: {
    marginTop: 10,
    borderRadius: 15,
  },
});

export default TitleCard;
