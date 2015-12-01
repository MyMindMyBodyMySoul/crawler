using System;
using AlexaCountryExtractor;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace UnitTestProject2
{
    [TestClass]
    public class UnitTest1
    {
        [TestMethod]
        public void TestMethod1()
        {
            var eh = new ExtHtml();

            var a1 = eh.GetCountries();
            //var a2 = eh.GetTop500("de");
            var res = eh.GetAllCountriesTop500(a1);
        }
    }
}
