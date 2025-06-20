import { StyleSheet, View, Text, FlatList } from "react-native";

import Title from "../components/Title";
import Card from "../components/Card";
import CategoryCard from "../components/CategoryCard";
import { CATEGORIES } from "../data/dummy-data";

function CategoriesScreen({ onSelectCategory }) {
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
              <CategoryCard
                id={itemData.item.id}
                title={itemData.item.title}
                backgroundColor={itemData.item.color}
                onSelectCategory={onSelectCategory}
              />
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
});

export default CategoriesScreen;
