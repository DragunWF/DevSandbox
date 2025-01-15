package com.codewithmosh.prototype;

public class Text implements Component {
    private String content;

    public Text(String content) {
        this.content = content;
    }

    public String getContent() {
        return content;
    }

    @Override
    public Text clone() {
        return new Text(this.getContent());
    }
}
