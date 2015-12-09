using System;
using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using HtmlAgilityPack;


namespace AlexaCountryExtractor
{
    public class ExtHtml
    {
        public Dictionary<string, string> GetCountries()
        {
            string url = "http://www.alexa.com/topsites/countries";
            var Webget = new HtmlWeb();
            var doc = Webget.Load(url);
            var res = new Dictionary<string, string>();

            foreach (HtmlNode node in doc.DocumentNode.SelectNodes("//ul[@class='countries span3']//li//a"))
            {
                res.Add(node.ChildNodes[0].InnerHtml, GetLast(node.Attributes[0].Value, 2));
            }

            return res;
        }

        public List<string> GetTop500(string SC = "CL")
        {

            const string PATTERN = "http://www.alexa.com/topsites/countries;{0}/{1}";
            var res = new List<string>();
            for (int i = 0; i < 20; i++)
            {

                var url = String.Format(PATTERN, i, SC.ToUpper());
                var Webget = new HtmlWeb();
                var doc = Webget.Load(url);
                foreach (HtmlNode node in doc.DocumentNode.SelectNodes("//p[@class='desc-paragraph']//a"))
                {
                    res.Add(node.ChildNodes[0].InnerHtml);
                }

            }

            return res;
        }

        public Dictionary<string, List<string>> GetAllCountriesTop500(Dictionary<string,string> countries)
        {
            var result = new Dictionary<string, List<string>>();
                Parallel.ForEach(countries, country =>
                {


                    result.Add(country.Key, GetTop500(country.Value));

                });

            return result;
        }
        private static string GetLast(string source, int tail_length)
        {
            if (tail_length >= source.Length)
                return source;
            return source.Substring(source.Length - tail_length);
        }
    }
}
