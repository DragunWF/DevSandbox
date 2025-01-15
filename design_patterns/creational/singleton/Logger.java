package com.codewithmosh.singleton;

public class Logger {
    private String fileName;
    private static Logger instance = new Logger();

    private Logger() {
    }

    public void write(String message) {
        System.out.println("Writing a message to the log.");
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public static Logger getInstance() {
        return instance;
    }
}
