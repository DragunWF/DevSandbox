class Program
{
    static void Main()
    {
        string path = "dragun.txt";
        string[] friends = { "DragunWF", "CPT", "Luq", "Mortis", "Larry" };

        using (StreamWriter writer = new StreamWriter(path))
        {
            Console.WriteLine("Starting write operation");
            writer.WriteLine($"Friend List of {friends.Length}:");
            for (int i = 1; i <= friends.Length; i++)
            {
                writer.WriteLine($"{i}. {friends[i - 1]}");
                Console.WriteLine($"Wrote friend to friend list ({i})");
            }
            Console.WriteLine("Friend list writing operation completed...");
        }

        Console.WriteLine("\n================================\n");

        using (StreamReader reader = new StreamReader(path))
        {
            Console.WriteLine("Starting read operation...");
            string line;
            int lineCount = 0;
            while ((line = reader.ReadLine()) != null)
            {
                Console.WriteLine($"Line {++lineCount}: {line}");
            }
            Console.WriteLine("Read operation completed");
        }

        Console.WriteLine();
    }
}
