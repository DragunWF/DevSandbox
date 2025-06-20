import { StyleSheet, View, Text, FlatList } from "react-native";

import Title from "../components/Title";
import Card from "../components/Card";
import { CATEGORIES } from "../data/dummy-data";

function CategoriesScreen() {
  return (
    <View style={styles.screen}>
      <View style={styles.headContainer}>
        <Card style={styles.titleCardContainer}>
          <Title>Meal Categories</Title>
        </Card>
      </View>
      <View style={styles.categoriesContainer}>
        <FlatList
          data={CATEGORIES}
          renderItem={(itemData) => {
            return (
              <Card
                style={styles.categoryCard}
                backgroundColor={itemData.item.color}
              >
                <Text style={styles.categoryText}>{itemData.item.title}</Text>
              </Card>
            );
          }}
          keyExtractor={(item) => item.id}
          alwaysBounceVertical={false}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    justifyContent: "flex-start", // Align to top
    alignItems: "center",
  },
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
  categoryCard: {
    marginTop: 15,
    borderRadius: 20,
    paddingHorizontal: 100,
  },
  categoryText: {
    fontFamily: "poppins",
    fontSize: 16,
    color: "white",
    elevation: 4,
    shadowColor: "black",
    shadowOffset: { width: 4, height: 4 },
    shadowRadius: 4,
    shadowOpacity: 0.5,
  },
});

export default CategoriesScreen;
