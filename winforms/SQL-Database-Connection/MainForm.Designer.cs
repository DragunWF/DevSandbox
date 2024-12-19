namespace SQL_Database_Connection
{
    partial class MainForm
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            displayDataBtn = new Button();
            dataTxt = new RichTextBox();
            label1 = new Label();
            idTxt = new TextBox();
            nameTxt = new TextBox();
            descriptionTxt = new TextBox();
            insertDataBtn = new Button();
            label2 = new Label();
            SuspendLayout();
            // 
            // displayDataBtn
            // 
            displayDataBtn.Location = new Point(122, 240);
            displayDataBtn.Name = "displayDataBtn";
            displayDataBtn.Size = new Size(101, 32);
            displayDataBtn.TabIndex = 0;
            displayDataBtn.Text = "Display Data";
            displayDataBtn.UseVisualStyleBackColor = true;
            displayDataBtn.Click += displayDataBtn_Click;
            // 
            // dataTxt
            // 
            dataTxt.Location = new Point(12, 45);
            dataTxt.Name = "dataTxt";
            dataTxt.Size = new Size(318, 189);
            dataTxt.TabIndex = 1;
            dataTxt.Text = "";
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Font = new Font("Segoe UI", 14.25F, FontStyle.Bold, GraphicsUnit.Point, 0);
            label1.Location = new Point(58, 9);
            label1.Name = "label1";
            label1.Size = new Size(228, 25);
            label1.TabIndex = 2;
            label1.Text = "Data from SQL Database";
            // 
            // idTxt
            // 
            idTxt.Location = new Point(21, 278);
            idTxt.Name = "idTxt";
            idTxt.Size = new Size(95, 23);
            idTxt.TabIndex = 3;
            // 
            // nameTxt
            // 
            nameTxt.Location = new Point(122, 278);
            nameTxt.Name = "nameTxt";
            nameTxt.Size = new Size(100, 23);
            nameTxt.TabIndex = 4;
            // 
            // descriptionTxt
            // 
            descriptionTxt.Location = new Point(228, 278);
            descriptionTxt.Name = "descriptionTxt";
            descriptionTxt.Size = new Size(102, 23);
            descriptionTxt.TabIndex = 5;
            // 
            // insertDataBtn
            // 
            insertDataBtn.Location = new Point(122, 307);
            insertDataBtn.Name = "insertDataBtn";
            insertDataBtn.Size = new Size(100, 23);
            insertDataBtn.TabIndex = 6;
            insertDataBtn.Text = "Insert Data";
            insertDataBtn.UseVisualStyleBackColor = true;
            insertDataBtn.Click += insertDataBtn_Click;
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.Font = new Font("Segoe UI", 6F);
            label2.Location = new Point(21, 314);
            label2.Name = "label2";
            label2.Size = new Size(84, 11);
            label2.TabIndex = 7;
            label2.Text = "ID, Name, Description";
            // 
            // MainForm
            // 
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(342, 341);
            Controls.Add(label2);
            Controls.Add(insertDataBtn);
            Controls.Add(descriptionTxt);
            Controls.Add(nameTxt);
            Controls.Add(idTxt);
            Controls.Add(label1);
            Controls.Add(dataTxt);
            Controls.Add(displayDataBtn);
            Name = "MainForm";
            Text = "SQL Database Form";
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Button displayDataBtn;
        private RichTextBox dataTxt;
        private Label label1;
        private TextBox idTxt;
        private TextBox nameTxt;
        private TextBox descriptionTxt;
        private Button insertDataBtn;
        private Label label2;
    }
}
