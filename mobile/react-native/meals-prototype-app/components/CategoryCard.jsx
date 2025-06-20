import { StyleSheet, Text, Pressable } from "react-native";
import Card from "./Card";

function CategoryCard({ id, title, backgroundColor, onSelectCategory }) {
  return (
    <Pressable onPress={() => onSelectCategory(id)}>
      <Card style={styles.categoryCard} backgroundColor={backgroundColor}>
        <Text style={styles.categoryText}>{title}</Text>
      </Card>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  categoryCard: {
    marginTop: 15,
    borderRadius: 20,
    paddingHorizontal: 100,
    borderWidth: 2,
    borderColor: "black",
  },
  categoryText: {
    fontFamily: "poppins",
    fontSize: 16,
    color: "white",
    elevation: 4,
    shadowColor: "black",
    shadowOffset: { width: 5, height: 5 },
    shadowRadius: 4,
    shadowOpacity: 1,
  },
});

export default CategoryCard;
