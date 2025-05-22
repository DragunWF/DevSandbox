enum AccountType {
    USER,
    ADMIN
}

enum GovernmentType {
    LOCAL,
    NATIONAL
}

public class EnumTest {
    public static void main(String[] args) {
        GovernmentType governmentType = GovernmentType.LOCAL;
        AccountType accountType = AccountType.USER;

        System.out.println(governmentType);

        if (accountType == AccountType.USER) {
            System.out.println("Account type is a user!");
        } else {
            System.out.println("Account type is an admin!");
        }

        if (governmentType == GovernmentType.LOCAL) {
            System.out.println("Government type is local!");
        } else {
            System.out.println("Government type is national!");
        }
    }
}
