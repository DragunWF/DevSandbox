import java.util.Stack;

public class Exercise {
    public static void main(String[] args) {
        Document doc = new Document();
        Object[][] data = {
                { "Hello World!", "Poppins", 12 },
                { "Goodbye World!", "Arial", 16 },
                { "Dance of the dreams", "Calibri", 18 }
        };
        for (Object[] obj : data) {
            doc.setContent((String) obj[0]);
            doc.setFontName((String) obj[1]);
            doc.setFontSize((int) obj[2]);
            doc.saveState();
        }

        for (int i = 0; i < data.length; i++) {
            doc.restoreState();
            System.out.println(doc.toString());
        }
        doc.restoreState();
    }
}

class Caretaker {
    private Stack<Memento> mementos = new Stack<>();

    public boolean isEmpty() {
        return mementos.empty();
    }

    public void push(Memento memento) {
        mementos.push(memento);
    }

    public Memento pop() {
        return mementos.pop();
    }
}

class Memento {
    private String content;
    private String fontName;
    private int fontSize;

    public Memento(String content, String fontName, int fontSize) {
        this.content = content;
        this.fontName = fontName;
        this.fontSize = fontSize;
    }

    public String getContent() {
        return content;
    }

    public String getFontName() {
        return fontName;
    }

    public int getFontSize() {
        return fontSize;
    }
}

class Document {
    private String content;
    private String fontName;
    private int fontSize;
    private Caretaker states = new Caretaker();

    public void saveState() {
        states.push(new Memento(content, fontName, fontSize));
    }

    public void restoreState() {
        if (!states.isEmpty()) {
            Memento previousState = states.pop();
            content = previousState.getContent();
            fontName = previousState.getFontName();
            fontSize = previousState.getFontSize();
        } else {
            System.out.println("There is nothing to restore!");
        }
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getFontName() {
        return fontName;
    }

    public void setFontName(String fontName) {
        this.fontName = fontName;
    }

    public int getFontSize() {
        return fontSize;
    }

    public void setFontSize(int fontSize) {
        this.fontSize = fontSize;
    }

    @Override
    public String toString() {
        return "Document{" +
                "content='" + content + '\'' +
                ", fontName='" + fontName + '\'' +
                ", fontSize=" + fontSize +
                '}';
    }
}
