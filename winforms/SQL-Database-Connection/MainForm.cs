using System.Data;
using System.Data.SqlClient;

namespace SQL_Database_Connection
{
    public partial class MainForm : Form
    {
        // Replace this connection string with your actual database
        private string conString = "Data Source=DRAGUNWF\\SQLEXPRESS;Initial Catalog=TestDB;Integrated Security=True";

        public MainForm()
        {
            InitializeComponent();
        }

        private void displayDataBtn_Click(object sender, EventArgs e)
        {
            dataTxt.Text = "";
            using (SqlConnection con = new SqlConnection(conString))
            {
                try
                {
                    con.Open();
                    string query = "SELECT * FROM users";
                    using (SqlCommand cmd = new SqlCommand(query, con))
                    {
                        SqlDataAdapter adapter = new SqlDataAdapter(cmd);
                        DataTable dataTable = new DataTable();
                        adapter.Fill(dataTable);

                        // Build a string from the data
                        string result = "";
                        foreach (DataRow row in dataTable.Rows)
                        {
                            foreach (var item in row.ItemArray)
                            {
                                result += item.ToString() + " ";  // Append each column value with a space
                            }
                            result += Environment.NewLine;  // New line after each row
                        }

                        // Display the result in a MessageBox
                        dataTxt.Text = result;
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Error: " + ex.Message);
                }
            }
        }

        private void insertDataBtn_Click(object sender, EventArgs e)
        {
            using (SqlConnection con = new SqlConnection(conString))
            {
                try
                {
                    con.Open();
                    string query = "INSERT INTO users VALUES (@id, @name, @description)";
                    using (SqlCommand cmd = new SqlCommand(query, con))
                    {
                        cmd.Parameters.AddWithValue("@id", idTxt.Text); 
                        cmd.Parameters.AddWithValue("@name", nameTxt.Text);
                        cmd.Parameters.AddWithValue("@description", descriptionTxt.Text);

                        int rowsAffected = cmd.ExecuteNonQuery();
                        MessageBox.Show($"{rowsAffected} row(s) inserted.");
                    }
                    idTxt.Text = "";
                    nameTxt.Text = "";
                    descriptionTxt.Text = "";
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Error: " + ex.Message);
                }
            }
        }
    }
}
