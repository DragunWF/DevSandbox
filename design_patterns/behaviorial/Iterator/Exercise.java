// My answer to Mosh Hamedani's Course on Design Patterns, Iterator Pattern Exercise

import java.util.ArrayList;
import java.util.List;

public class Exercise {
  public static void main(String[] args) {
    String[] productNames = { "Apple", "Keyboard", "iPhone 15", "Mouse", "Windows Laptop" };
    ProductCollection collection = new ProductCollection();
    for (int i = 0, id = 1; i < productNames.length; i++, id++) {
      collection.add(new Product(id, productNames[i]));
    }
    Iterator<Product> productIterator = collection.createIterator();
    while (productIterator.hasNext()) {
      System.out.println(productIterator.current().toString());
      productIterator.next();
    }
  }
}

interface Iterator<T> {
  boolean hasNext();

  T current();

  void next();
}

class Product {
  private int id;
  private String name;

  public Product(int id, String name) {
    this.id = id;
    this.name = name;
  }

  @Override
  public String toString() {
    return "Product{" +
        "id=" + id +
        ", name='" + name + '\'' +
        '}';
  }
}

class ProductCollection {
  private List<Product> products = new ArrayList<>();

  public void add(Product product) {
    products.add(product);
  }

  public Iterator<Product> createIterator() {
    return new ListIterator(this);
  }

  class ListIterator implements Iterator<Product> {
    private ProductCollection collection;
    private int index = 0;

    public ListIterator(ProductCollection collection) {
      this.collection = collection;
    }

    public boolean hasNext() {
      return index < collection.products.size();
    }

    public Product current() {
      return collection.products.get(index);
    }

    public void next() {
      index++;
    }
  }
}