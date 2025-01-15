// My solution to Mosh Hamedani's Design Patterns Course Exericse, Strategy Pattern

public class Exercise {
    public static void main(String[] args) {
        new ChatClient(new AES()).send("Hello");
        new ChatClient(new DES()).send("Goodbye");
    }
}

interface EncryptionAlgorithm {
    void encrypt();
}

class ChatClient {
    private EncryptionAlgorithm encryptionAlgorithm;

    public ChatClient(EncryptionAlgorithm encryptionAlgorithm) {
        this.encryptionAlgorithm = encryptionAlgorithm;
    }

    public void send(String message) {
        encryptionAlgorithm.encrypt();
        System.out.println("Sending the encrypted message...");
    }
}

class AES implements EncryptionAlgorithm {
    public void encrypt() {
        System.out.println("Encrypting message using AES");
    }
}

class DES implements EncryptionAlgorithm {
    public void encrypt() {
        System.out.println("Encrypting message using DES");
    }
}