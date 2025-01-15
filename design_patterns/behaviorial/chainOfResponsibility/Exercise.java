public class Exercise {
    public static void main(String[] args) {
        DataReader reader = new DataReader();
        reader.read("dragun.txt");
        reader.read("luq.numbers");
    }
}

class DataReader {
    public void read(String fileName) {
        var textFileExtension = new TextFileExtension(null);
        var excelFileExtension = new ExcelFileExtension(textFileExtension);
        var numbersFileExtension = new NumbersFileExtension(excelFileExtension);
        var quickBooksFileExtension = new QuickBooksFileExtension(numbersFileExtension);

        quickBooksFileExtension.handle(fileName);
    }
}

abstract class Handler {
    private Handler next;

    public Handler(Handler next) {
        this.next = next;
    }

    public void handle(String fileExtension) {
        if (!doHandle(fileExtension) && next != null) {
            next.handle(fileExtension);
        }
    }

    abstract protected boolean doHandle(String fileExtension);
}

class ExcelFileExtension extends Handler {
    public ExcelFileExtension(Handler next) {
        super(next);
    }

    @Override
    public boolean doHandle(String fileExtension) {
        System.out.println("Excel File Extension");
        return fileExtension.endsWith(".xls");
    }
}

class NumbersFileExtension extends Handler {
    public NumbersFileExtension(Handler next) {
        super(next);
    }

    @Override
    public boolean doHandle(String fileExtension) {
        System.out.println("Numbers File Extension");
        return fileExtension.endsWith(".numbers");
    }
}

class QuickBooksFileExtension extends Handler {
    public QuickBooksFileExtension(Handler next) {
        super(next);
    }

    @Override
    public boolean doHandle(String fileExtension) {
        System.out.println("Quick Books File Extension");
        return fileExtension.endsWith(".qbw");
    }
}

class TextFileExtension extends Handler {
    public TextFileExtension(Handler next) {
        super(next);
    }

    @Override
    public boolean doHandle(String fileExtension) {
        System.out.println("Text File Extension");
        return fileExtension.endsWith(".txt");
    }
}