import java.util.ArrayList;
import java.util.List;
import java.io.IOException;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class Demo {
    public static void show() throws IOException {
        var document = new Document();
        document.add(new Text("Hello World"));
        document.add(new Image("pic1.jpg"));

        document.export(ExportFormat.HTML, "export.html");

        // Only writes the text elements to the file
        document.export(ExportFormat.TEXT, "export.txt");
    }
}

interface Element {
}

enum ExportFormat {
    HTML,
    TEXT,
    PDF,
}

class HtmlDocument {
    private List<HtmlElement> elements = new ArrayList<>();

    public void add(HtmlElement element) {
        elements.add(element);
    }

    @Override
    public String toString() {
        var builder = new StringBuilder();
        builder.append("<html>");
        for (HtmlElement element : elements)
            builder.append(element.toString());
        builder.append("</html>");
        return builder.toString();
    }
}

class HtmlElement {
}

class HtmlImage extends HtmlElement {
    private String source;

    public HtmlImage(String source) {
        this.source = source;
    }

    @Override
    public String toString() {
        return String.format("<img src=\"%s\" />", source);
    }
}

class HtmlParagraph extends HtmlElement {
    private String text;

    public HtmlParagraph(String text) {
        this.text = text;
    }

    @Override
    public String toString() {
        return String.format("<p>%s</p>", text);
    }
}

class Document {
    private List<Element> elements = new ArrayList<>();

    public void add(Element element) {
        elements.add(element);
    }

    public void export(ExportFormat format, String fileName) throws IOException {
        String content = "";

        if (format == ExportFormat.HTML) {
            var document = new HtmlDocument();

            for (Element element : elements) {
                if (element instanceof Text) {
                    var text = ((Text) element).getContent();
                    document.add(new HtmlParagraph(text));
                } else if (element instanceof Image) {
                    var source = ((Image) element).getSource();
                    document.add(new HtmlImage(source));
                }
            }

            content = document.toString();
        } else if (format == ExportFormat.TEXT) {
            var builder = new StringBuilder();

            for (Element element : elements) {
                if (element instanceof Text) {
                    var text = ((Text) element).getContent();
                    builder.append(text);
                }
            }

            content = builder.toString();
        }

        var writer = new FileWriter(fileName);
        writer.write(content);
        writer.close();
    }
}

class Image implements Element {
    private String source;

    public Image(String source) {
        this.source = source;
    }

    public String getSource() {
        return source;
    }
}

class Text implements Element {
    private String content;

    public Text(String content) {
        this.content = content;
    }

    public String getContent() {
        return content;
    }
}