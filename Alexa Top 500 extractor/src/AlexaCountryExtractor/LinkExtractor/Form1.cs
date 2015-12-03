using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using AlexaCountryExtractor;

namespace LinkExtractor
{
    public partial class Form1 : Form
    {
        private string path;
        private ExtHtml alexa;
        private Dictionary<string, string> countries;
        private Dictionary<string, List<string>> result;

        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            alexa = new ExtHtml();
            countries = alexa.GetCountries();
            progressBar1.Maximum = countries.Count();
            result = new Dictionary<string, List<string>>();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            DialogResult result = folderBrowserDialog1.ShowDialog();
            if (result == DialogResult.OK)
            {
                button2.Enabled = true;
                //MessageBox.Show(folderBrowserDialog1.SelectedPath);
                path = folderBrowserDialog1.SelectedPath;
            }
        }

        private void button2_Click(object sender, EventArgs e)
        {
            this.Enabled = false;
            progressBar1.Style = ProgressBarStyle.Marquee;
            progressBar1.MarqueeAnimationSpeed = 100;
            Task.Factory.StartNew(() =>
            {
                Parallel.ForEach(countries, country =>
                {

                    var sites = alexa.GetTop500(country.Value);
                    result.Add(country.Key, sites);
                    using (StreamWriter writer = new StreamWriter(path + @"\" + country.Key + ".txt"))
                    {
                        foreach (var site in sites)
                        {
                            writer.Write(site + System.Environment.NewLine);
                        }
                        writer.Close();
                    }



                });
                MessageBox.Show(countries.Count + " countries done.");
                Application.Exit();
            }
                );
            
            
        }

        

       
    }
}
