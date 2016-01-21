var request = require("request");
var cheerio = require('cheerio');
var os = require("os");
var fs = require('fs');
var countries = [];
var count = 0;
//
//Save location:
//
var outputPath = './result/';



var url = "http://www.alexa.com/topsites/countries";
function getCountries(error, response, body) {
    if (!error && response.statusCode == 200) {
        var $ = cheerio.load(body);
        var a = $('.countries').each(function(i,ele)
        {
            $ = cheerio.load($(this).html());
            $('a').each(function(i,ele){
                countries[count] = $(this).attr('href').slice(-2);
                count++;
            });
        });
        var list = countries.join(',  ');
        console.log(list);
        CreateLinks();
    }
}
function CreateLinks(){
    //http://www.alexa.com/topsites/countries;0/AL
    //res =
    var pattern1 = "http://www.alexa.com/topsites/countries;";
    var pattern2 = "/";


    if (!fs.existsSync(outputPath)){
        fs.mkdirSync(outputPath);
    }
    for(var i = 0;i<count;i++)
    {
        fs.writeFile(outputPath + countries[i] + ".txt", '', function (err) {
            if (err) {
                return console.log(err);
            }
        });
    }
    var ctrr = 1;
    var ctrr2 = 1;

    countries.forEach(function(cnt)
    {
        ctrr++;
        setTimeout(function(){
        var pattern = [];
        for (var j = 0; j < 20; j++) {

             pattern[j] = pattern1 + j + pattern2 + cnt;
        }

        pattern.forEach(function(countryLink){
             ctrr2++;
            setTimeout(function()
            {
            request(countryLink, function (error, response, body) {
                if (!error && response.statusCode == 200) {
                    var $ = cheerio.load(body);
                    var a = $('.desc-paragraph').each(function(i,ele)
                    {
                        $ = cheerio.load($(this).html());
                        $('a').each(function(i,ele) {

                                fs.appendFile(outputPath + cnt + '.txt', $(this).text() + os.EOL, function (err) {
                                });
                                //console.log(cnt + " links Added");
                        });
                    });
                    console.log("Reading country: " + cnt);
                    console.log("Reading country link: " + countryLink);
                    console.log("");
                }});
            },100*ctrr2);});


    },200*ctrr);
    });
}

request(url, getCountries);



