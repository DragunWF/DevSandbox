public class Example {
    public static void main(String[] args) {
        HumanBuilder builder = new HumanBuilder();
        builder.setName("John").setAge(18);
        Human john = builder.buildHuman();
        System.out.println(john.getName());
        System.out.println(john.getAge());

        // example of an in-built class that utilizes the builder pattern
        StringBuilder sb = new StringBuilder();
        sb.append('a');
        System.out.println(sb.toString());
    }
}

class Human {
    private String name;
    private int age;

    public Human(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() {
        return name;
    }

    public int getAge() {
        return age;
    }
}

class HumanBuilder {
    private String name;
    private int age;

    public HumanBuilder setName(String name) {
        this.name = name;
        return this;
    }

    public HumanBuilder setAge(int age) {
        this.age = age;
        return this;
    }

    public Human buildHuman() {
        if (name.isEmpty() || age == 0) {
            return null;
        }
        return new Human(name, age);
    }
}
