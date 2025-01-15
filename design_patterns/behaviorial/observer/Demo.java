import java.util.ArrayList;
import java.util.List;

public class Demo {
    public static void main(String[] args) {
        StatusBar statusBar = new StatusBar();
        StockListView stockList = new StockListView();
        Stock stock = new Stock("PHP", 159.99f);

        statusBar.addStock(stock);
        stockList.addStock(stock);

        System.out.println("Base Values:");
        statusBar.show();
        stockList.show();

        stock.addObserver(statusBar);
        stock.addObserver(stockList);

        stock.setPrice(350.99f);
    }
}

interface Observer {
    void update(float price);
}

class Subject {
    private List<Observer> observers = new ArrayList<>();

    public void addObserver(Observer observer) {
        observers.add(observer);
    }

    public void notifyObservers(float price) {
        for (var observer : observers) {
            observer.update(price);
        }
    }
}

class StatusBar implements Observer {
    private List<Stock> stocks = new ArrayList<>();

    @Override
    public void update(float price) {
        System.out.println("Stock price was updated: " + price);
        show();
    }

    public void addStock(Stock stock) {
        stocks.add(stock);
    }

    public void show() {
        for (var stock : stocks)
            System.out.println(stock);
    }
}

class StockListView implements Observer {
    private List<Stock> stocks = new ArrayList<>();

    @Override
    public void update(float price) {
        System.out.println("A stock price was updated to " + price);
        show();
    }

    public void addStock(Stock stock) {
        stocks.add(stock);
    }

    public void show() {
        for (var stock : stocks)
            System.out.println(stock);
    }
}

class Stock extends Subject {
    private String symbol;
    private float price;

    public Stock(String symbol, float price) {
        this.symbol = symbol;
        this.price = price;
    }

    public float getPrice() {
        return price;
    }

    public void setPrice(float price) {
        this.price = price;
        notifyObservers(price);
    }

    @Override
    public String toString() {
        return "Stock{" +
                "symbol='" + symbol + '\'' +
                ", price=" + price +
                '}';
    }
}