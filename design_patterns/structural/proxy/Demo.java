import java.util.HashMap;
import java.util.Map;

public class Demo {
  public static void show() {
    var dbContext = new DbContext();

    // We read an object (eg a product) from a database.
    var product = dbContext.getProduct(1);

    // We modify the properties of the object in memory.
    product.setName("Updated Name");
    dbContext.markAsChanged(product);

    // DbContext should keep track of changed objects in memory.
    // When we call saveChanges(), it'll automatically generate
    // the right SQL statements to update our database.
    dbContext.saveChanges();

    // After saving the changes to the database, we can
    // change our in-memory object again and save the changes.
    product.setName("Another name");
    dbContext.markAsChanged(product);
    dbContext.saveChanges();
  }

  public static void main(String[] args) {
    show();
  }
}

interface Product {
  public int getId();

  public String getName();

  public void setName(String name);
}

class RealProduct implements Product {
  private int id;
  private String name;

  public RealProduct(int id) {
    this.id = id;
  }

  public int getId() {
    return id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }
}

class ProxyProduct implements Product {
  private RealProduct product;
  private int id;

  public ProxyProduct(int id) {
    this.id = id;
  }

  public int getId() {
    if (product == null) {
      product = new RealProduct(id);
    }
    return product.getId();
  }

  public String getName() {
    if (product == null) {
      product = new RealProduct(id);
    }
    return product.getName();
  }

  public void setName(String name) {
    if (product == null) {
      product = new RealProduct(id);
    }
    product.setName(name);
  }
}

class DbContext {
  private Map<Integer, ProxyProduct> updatedObjects = new HashMap<>();

  public ProxyProduct getProduct(int id) {
    // Automatically generate SQL statements
    // to read the product with the given ID.
    System.out.printf("SELECT * FROM products WHERE product_id = %d \n", id);

    // Simulate reading a product object from a database.
    var product = new ProxyProduct(id);
    product.setName("Product 1");

    return product;
  }

  public void saveChanges() {
    // Automatically generate SQL statements
    // to update the database.
    for (var updatedObject : updatedObjects.values())
      System.out.printf("UPDATE products SET name = '%s' WHERE product_id = %d \n", updatedObject.getName(),
          updatedObject.getId());

    updatedObjects.clear();
  }

  public void markAsChanged(ProxyProduct product) {
    updatedObjects.put(product.getId(), product);
  }
}