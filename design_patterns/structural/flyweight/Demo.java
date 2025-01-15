import java.util.HashMap;

public class Demo {
  public static void show() {
    var sheet = new SpreadSheet();
    sheet.setContent(0, 0, "Hello");
    sheet.setContent(1, 0, "World");
    sheet.setFontFamily(0, 0, "Arial");
    sheet.render();
  }

  public static void main(String[] args) {
    show();
  }
}

class Font {
  private String fontFamily;
  private int fontSize;
  private boolean isBold;

  public Font(String fontFamily) {
    this.fontFamily = fontFamily;
  }

  public String getFontFamily() {
    return fontFamily;
  }

  public void setFontFamily(String fontFamily) {
    this.fontFamily = fontFamily;
  }

  public int getFontSize() {
    return fontSize;
  }

  public void setFontSize(int fontSize) {
    this.fontSize = fontSize;
  }

  public boolean isBold() {
    return isBold;
  }

  public void setBold(boolean bold) {
    isBold = bold;
  }
}

class FontFactory {
  private static HashMap<String, Font> fontMap = new HashMap<>();

  public Font getFont(String fontFamily) {
    if (!fontMap.containsKey(fontFamily)) {
      fontMap.put(fontFamily, new Font(fontFamily));
    }
    return fontMap.get(fontFamily);
  }
}

class Cell {
  private final int row;
  private final int column;
  private String content;
  private Font font;

  public Cell(int row, int column) {
    this.row = row;
    this.column = column;
  }

  public void setFontFamily(String fontFamily) {
    font = new FontFactory().getFont(fontFamily);
  }

  public String getFontFamily() {
    return font.getFontFamily();
  }

  public void setContent(String content) {
    this.content = content;
  }

  public String getContent() {
    return content;
  }

  public void render() {
    System.out.printf("(%d, %d): %s [%s]\n", row, column, content, font.getFontFamily());
  }
}

class SpreadSheet {
  private final int MAX_ROWS = 3;
  private final int MAX_COLS = 3;

  // In a real app, these values should not be hardcoded here.
  // They should be read from a configuration file.
  private final String fontFamily = "Times New Roman";
  private final int fontSize = 12;
  private final boolean isBold = false;

  private Cell[][] cells = new Cell[MAX_ROWS][MAX_COLS];

  public SpreadSheet() {
    generateCells();
  }

  public void setContent(int row, int col, String content) {
    ensureCellExists(row, col);

    cells[row][col].setContent(content);
  }

  public void setFontFamily(int row, int col, String fontFamily) {
    ensureCellExists(row, col);

    var cell = cells[row][col];
    cells[row][col].setFontFamily(fontFamily);
  }

  private void ensureCellExists(int row, int col) {
    if (row < 0 || row >= MAX_ROWS)
      throw new IllegalArgumentException();

    if (col < 0 || col >= MAX_COLS)
      throw new IllegalArgumentException();
  }

  private void generateCells() {
    for (var row = 0; row < MAX_ROWS; row++)
      for (var col = 0; col < MAX_COLS; col++) {
        var cell = new Cell(row, col);
        cell.setFontFamily(fontFamily);
        cells[row][col] = cell;
      }
  }

  public void render() {
    for (var row = 0; row < MAX_ROWS; row++)
      for (var col = 0; col < MAX_COLS; col++)
        cells[row][col].render();
  }
}