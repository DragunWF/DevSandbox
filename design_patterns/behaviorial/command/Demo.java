import java.util.Stack;

public class Demo {
    public static void main(String[] args) {
        VideoEditor videoEditor = new VideoEditor();
        History history = new History();

        UndoCommand undoCommand = new UndoCommand(history);
        AddTextCommand addTextCommand = new AddTextCommand(videoEditor, history, "Dragun");
        RemoveTextCommand removeTextCommand = new RemoveTextCommand(videoEditor, history);
        AddContrastCommand addContrastCommand = new AddContrastCommand(videoEditor, history, 1.5f);

        System.out.println("Initial Value of Video Editor: ");
        System.out.println(videoEditor.toString());

        addTextCommand.execute();
        addContrastCommand.execute();

        System.out.println("After execution of add commands:");
        System.out.println(videoEditor.toString());

        removeTextCommand.execute();

        System.out.println("After execution of remove command:");
        System.out.println(videoEditor.toString());

        undoCommand.execute();
        undoCommand.execute();

        System.out.println("After execution of undo command 2 times:");
        System.out.println(videoEditor.toString());
    }
}

class VideoEditor {
    private float contrast = 0.5f;
    private String text;

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public void removeText() {
        this.text = "";
    }

    public float getContrast() {
        return contrast;
    }

    public void setContrast(float contrast) {
        this.contrast = contrast;
    }

    @Override
    public String toString() {
        return "VideoEditor{" +
                "contrast=" + contrast +
                ", text='" + text + '\'' +
                '}';
    }
}

class History {
    private static Stack<UndoableCommand> history = new Stack<>();

    public void addChange(UndoableCommand command) {
        history.push(command);
    }

    public void undoChange() {
        if (history.size() > 0) {
            history.pop().unexecute();
        }
    }
}

interface Command {
    void execute();
}

interface UndoableCommand extends Command {
    void unexecute();
}

class UndoCommand implements Command {
    private History history;

    public UndoCommand(History history) {
        this.history = history;
    }

    @Override
    public void execute() {
        history.undoChange();
    }
}

class AddTextCommand implements UndoableCommand {
    private VideoEditor videoEditor;
    private History history;
    private String prevContent;
    private String text;

    public AddTextCommand(VideoEditor videoEditor, History history, String text) {
        this.videoEditor = videoEditor;
        this.history = history;
        this.text = text;
    }

    @Override
    public void execute() {
        prevContent = videoEditor.getText();
        history.addChange(this);
        videoEditor.setText(text);
    }

    @Override
    public void unexecute() {
        videoEditor.setText(prevContent);
    }
}

class RemoveTextCommand implements UndoableCommand {
    private VideoEditor videoEditor;
    private History history;
    private String prevContent;

    public RemoveTextCommand(VideoEditor videoEditor, History history) {
        this.videoEditor = videoEditor;
        this.history = history;
    }

    @Override
    public void execute() {
        prevContent = videoEditor.getText();
        history.addChange(this);
        videoEditor.removeText();
    }

    @Override
    public void unexecute() {
        videoEditor.setText(prevContent);
    }
}

class AddContrastCommand implements UndoableCommand {
    private VideoEditor videoEditor;
    private History history;
    private float prevContent;
    private float contrast;

    public AddContrastCommand(VideoEditor videoEditor, History history, float contrast) {
        this.videoEditor = videoEditor;
        this.history = history;
        this.contrast = contrast;
    }

    @Override
    public void execute() {
        prevContent = videoEditor.getContrast();
        history.addChange(this);
        videoEditor.setContrast(contrast);
    }

    @Override
    public void unexecute() {
        videoEditor.setContrast(prevContent);
    }
}