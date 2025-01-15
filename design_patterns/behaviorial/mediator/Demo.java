import java.util.List;
import java.util.ArrayList;

public class Demo {
    public static void main(String[] args) {
        new DialogBox().simulateUserInteraction();
    }
}

interface EventHandler {
    void handle();
}

class DialogBox {
    private CheckBox checkBox = new CheckBox();
    private TextBox usernameTextBox = new TextBox();
    private TextBox passwordTextBox = new TextBox();
    private SignUpButton signUpButton = new SignUpButton();

    public DialogBox() {
        usernameTextBox.addEventHandler(this::stateChanged);
        passwordTextBox.addEventHandler(this::stateChanged);
        checkBox.addEventHandler(this::stateChanged);
    }

    public void simulateUserInteraction() {
        System.out.println("Simulating user interaction");
        showSignUpButtonState();

        System.out.println("Checking text box");
        checkBox.setChecked(true);
        showSignUpButtonState();

        System.out.println("Entering username");
        usernameTextBox.setText("Dragun");
        showSignUpButtonState();

        System.out.println("Entering password");
        passwordTextBox.setText("password123");
        showSignUpButtonState();
    }

    private void stateChanged() {
        signUpButton.setEnabled(
                !usernameTextBox.getText().isEmpty() &&
                        !passwordTextBox.getText().isEmpty() &&
                        checkBox.isChecked());
    }

    private void showSignUpButtonState() {
        System.out.printf(
                "Sign Up Button Enabled: %s\n",
                signUpButton.isEnabled());
    }
}

abstract class UIControl {
    private List<EventHandler> eventHandlers = new ArrayList<>();

    public void addEventHandler(EventHandler handler) {
        eventHandlers.add(handler);
    }

    protected void notifyEventHandlers() {
        for (EventHandler handler : eventHandlers) {
            handler.handle();
        }
    }
}

class CheckBox extends UIControl {
    private boolean checked = false;

    public boolean isChecked() {
        return checked;
    }

    public void setChecked(boolean checked) {
        this.checked = checked;
        notifyEventHandlers();
    }
}

class TextBox extends UIControl {
    private String text = "";

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
        notifyEventHandlers();
    }
}

class SignUpButton extends UIControl {
    private boolean enabled = false;

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
        notifyEventHandlers();
    }
}