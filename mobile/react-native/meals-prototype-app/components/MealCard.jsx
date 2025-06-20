import { StyleSheet, View, Text } from "react-native";
import Card from "./Card";
import Title from "./Title";
import PrimaryButton from "./PrimaryButton";

function MealCard({
  id,
  title,
  affordability,
  complexity,
  onButtonPressed: onOpenMeal,
}) {
  function openMealHandler() {
    onOpenMeal(id);
  }

  return (
    <Card style={styles.cardContainer}>
      <Title style={styles.title}>{title}</Title>
      <Text style={styles.cardText}>Affordability: {affordability}</Text>
      <Text style={styles.cardText}>Complexity: {complexity}</Text>
      <PrimaryButton onPress={openMealHandler} style={styles.button}>
        See More
      </PrimaryButton>
    </Card>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    margin: 20,
    paddingHorizontal: 15,
    paddingTop: 15,
    paddingBottom: 20,
  },
  title: {
    fontSize: 18,
    marginBottom: 10,
  },
  cardText: {
    fontSize: 16,
    color: "white",
  },
  button: {
    marginTop: 15,
  },
});

export default MealCard;
