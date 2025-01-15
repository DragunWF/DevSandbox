// My submission to Template Method exercise

public class Exercise {
    public static void main(String[] args) {
        CustomWindow window = new CustomWindow();
        window.close();
    }
}

abstract class Window {
    public void close() {
        // TODO: custom windows may need to execute some code before the window
        // is closed.

        preCloseExecute();

        System.out.println("Removing the window from the screen");

        postCloseExecute();

        // TODO: custom windows may need to execute some code after the window
        // is closed.
    }

    protected abstract void preCloseExecute();

    protected abstract void postCloseExecute();
}

class CustomWindow extends Window {
    @Override
    protected void preCloseExecute() {
        System.out.println("Executing code before the window is closed");
    }

    @Override
    protected void postCloseExecute() {
        System.out.println("Executing code after the window is closed");
    }
}