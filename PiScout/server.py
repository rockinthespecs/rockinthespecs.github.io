import cherrypy
import sqlite3 as sql
import os
import json
from ast import literal_eval
import requests
import math
from statistics import mode
from ipaddress import IPV6LENGTH
from event import CURRENT_EVENT

# Update this value before every event
# Use the event codes given by thebluealliance
DEFAULT_MODE = 'averages'

class ScoutServer(object):
    @cherrypy.expose
    def index(self, m='', e=''):
        
        #First part is to handle event selection. When the event is changed, a POST request is sent here.
        illegal = '' #i competely forget what this variable does, just leave it
        if e != '':
            if os.path.isfile('data_' + e + '.db'):
                cherrypy.session['event'] = e
            else:
                illegal = e
        if 'event' not in cherrypy.session:
            cherrypy.session['event'] = CURRENT_EVENT
            
        if m != '':
            cherrypy.session['mode'] = m
        if 'mode' not in cherrypy.session:
            cherrypy.session['mode'] = DEFAULT_MODE

        #This section generates the table of averages
        table = ''
        conn = sql.connect(self.datapath())
        if(cherrypy.session['mode'] == "averages"):
            data = conn.cursor().execute('SELECT * FROM averages ORDER BY apr DESC').fetchall()
        elif (cherrypy.session['mode'] == "maxes"):
            data = conn.cursor().execute('SELECT * FROM maxes ORDER BY apr DESC').fetchall()
        elif (cherrypy.session['mode'] == "noD"):
            data = conn.cursor().execute('SELECT * FROM noDefense ORDER BY apr DESC').fetchall()
        else:
            data = conn.cursor().execute('SELECT * from lastThree ORDER BY apr DESC').fetchall()
        conn.close()
        for team in data: #this table will need to change based on the number of columns on the main page
            table += '''
            <tr>
                <td><a href="team?n={0}">{0}</a></td>
                <td>{1}</td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td>{5}</td>
                <td>{6}</td>
                <td>{7}</td>
                <td>{8}</td>
            </tr>
            '''.format(team[0], team[1], team[2], team[3], round(team[2] + team[3], 2), team[5], team[6], team[7], team[8])
        #in this next block, update the event list and the column titles
        return '''
        <html>
            <head>
                <title>PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="./static/css/style.css" rel="stylesheet">
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
                <script>
                if (typeof jQuery === 'undefined')
                  document.write(unescape('%3Cscript%20src%3D%22/static/js/jquery.js%22%3E%3C/script%3E'));
                </script>
                <script type="text/javascript" src="./static/js/jquery.tablesorter.js"></script>
                <script>
                $(document).ready(function() {{
                    $("table").tablesorter();
                    $("#{1}").attr("selected", "selected");
                    $("#{2}").attr("selected", "selected");
                    console.log($("#{1}").selected);
                    {3}
                }});
                </script>
            </head>
            <body>
            <div style="max-width: 1000px; margin: 0 auto;">
                <br>
                <div style="vertical-align:top; float:left; width: 300px;">
                    <h1>PiScout</h1>
                    <h2>FRC Team 2067/238</h2>
                    <br><br>
                    <p class="main">Search Team</p>
                    <form method="get" action="team">
                        <input class="field" type="text" maxlength="4" name="n" autocomplete="off"/>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <br><br>
                    <p class="main">Main Display</p>
                    <form method="post" action="/">
                        <select class="fieldsm" name="m">
                            <option id="maxes" value="maxes">Maxes</option>
                            <option id="averages" value="averages">Averages</option>
                            <option id="noD" value="noD">No Defense</option>
                            <option id="lastThree" value="lastThree">Last 3</option>
                        </select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <br><br>
                     <p class="main">Change Event</p>
                    <form method="post" action="/">
                        <select class="fieldsm" name="e">
                          <option id="2017ctss" value="2017ctss">Suffield Shakedown</option>
                          <option id="2017wkzro" value="2017wkzro">Week Zero</option>
                          <option id="2017nhgrs" value="2017nhgrs">Granite State District Event</option>
                          <option id="2017ctwat" value="2017ctwat">Waterbury District Event</option>
                          <option id="2017mabos" value="2017mabos">Greater Boston District Event</option>
                          <option id="2017nhbed" value="2017nhbed">Southern New Hampshire District Event</option>
                          <option id="2017cthar" value="2017cthar">Hartford District Event</option>
                          <option id="2017necmp" value="2017necmp">NE District Championship</option>
						  <option id="2017dar" value="2017dar">Darwin @ Championship</option>
                        </select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <br><br>
                    <p class="main">Compare</p>
                    <form method="get" action="compare">
                        <select class="fieldsm" name="t">
                          <option value="team">Teams</option>
                          <option value="alliance">Alliances</option>
                        </select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <br><br>
                    <p class="main">View Matches</p>
                    <form method="get" action="matches">
                        <select class="fieldsm" name="n">
                          <option value="2067">2067 matches</option>
                          <option value="238">238 matches</option>
                          <option value="0">All matches</option>
                        </select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <form method="get" action="rankings">
                        <button class="submit" type="submit">Predict Rankings</button>
                    </form>
                </div>

                <div style="vertical-align:top; border 1px solid black; overflow: hidden">
                 <table style="font-size: 140%;" class="tablesorter">
                    <thead><tr>
                        <th>Team</th>
                        <th>APR</th>
                        <th>Auto Gears</th>
                        <th>Tele Gears</th>
                        <th>Total Gears</th>
                        <th>Auto kPa</th>
                        <th>Tele kPa</th>
                        <th>Climb</th>
                        <th>Defense</th>
                    </tr></thead>
                    <tbody>{0}</tbody>
                </table>
                </div>
            </div>
            </body>
        </html>'''.format(table, cherrypy.session['event'], cherrypy.session['mode'],
                          '''alert('There is no data for the event "{}"')'''.format(illegal) if illegal else '')

    # Show a detailed summary for a given team
    @cherrypy.expose()
    def team(self, n="2067"):
        if not n.isdigit():
            raise cherrypy.HTTPRedirect('/')
        if int(n)==666:
            raise cherrypy.HTTPError(403, 'Satan has commanded me to not disclose his evil strategy secrets.')
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        entries = cursor.execute('SELECT * FROM scout WHERE d0=? ORDER BY d1 DESC', (n,)).fetchall()
        averages = cursor.execute('SELECT * FROM averages WHERE team=?', (n,)).fetchall()
        assert len(averages) < 2 #ensure there aren't two entries for one team
        if len(averages):
            s = averages[0]
        else:
            s = [0]*8 #generate zeros if no data exists for the team yet

        comments = cursor.execute('SELECT * FROM comments WHERE team=?', (n,)).fetchall()
        conn.close()

        # Generate html for comments section
        commentstr = ''
        for comment in comments:
            commentstr += '<div class="commentbox"><p>{}</p></div>'.format(comment[1])

        #Iterate through all the data entries and generate some text to go in the main table
        #this entire section will need to change from year to year
        output = ''
        dataset = []
        for e in entries:
            # Important: the index of e refers to the number of the field set in main.py
            # For example e[1] gets value #1 from main.py
            dp = {"match": e[2], "autoshoot":0, "shoot":0, "autogears":0, "gears":0, "geardrop":0}
            a = ''
            a += 'baseline, ' if e[6] else ''
            a += 'side try, ' if e[19] else ''
            a += 'center try, ' if e[20] else ''
            a += 'side peg, ' if e[21] else ''
            a += 'center peg, ' if e[22] else ''
            dp['autogears'] += e[5]
            a += str(e[7]) + 'x low goal, ' if e[7] else ''
            a += str(e[8]) + 'x high goal, ' if e[8] else ''
            dp['autoshoot'] += e[7]/3 + e[8]

            d = ''
            d += str(e[13]) + 'x gears, ' if e[13] else ''
            d += str(e[14]) + 'x gears dropped, ' if e[14] else ''
            dp['gears'] += e[13]
            dp['geardrop'] += e[14]

            sh = ''
            sh += str(e[15]) + 'x low goal, ' if e[15] else ''
            sh += str(e[16]) + 'x high goal, ' if e[16] else ''
            dp['shoot'] += e[15]/9 + e[16]/3

            o = 'hang, ' if e[17] else 'failed hang, ' if e[18] else ''
            o += str(e[3]) + 'x foul, ' if e[3] else ''
            o += str(e[4]) + 'x tech foul, ' if e[4] else ''
            o += 'defense, ' if e[11] else ''
            o += 'feeder, ' if e[10] else ''
            o += 'defended, ' if e[12] else ''

            #Generate a row in the table for each match
            output += '''
            <tr {5}>
                <td>{0}</td>
                <td>{1}</td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td><a class="flag" href="javascript:flag({6}, {7});">X</a></td>
                <td><a class="edit" href="/edit?key={8}">E</a></td>
            </tr>'''.format(e[2], a[:-2], d[:-2], sh[:-2], o[:-2], 'style="color: #B20000"' if e[23] else '', e[2], e[23], e[0])
            for key,val in dp.items():
                dp[key] = round(val, 2)
            if not e[19]: #if flagged
                dataset.append(dp) #add it to dataset, which is an array of data that is fed into the graphs
        dataset.reverse() #reverse so that graph is in the correct order

        #Grab the image from the blue alliance
        imcode = ''
        headers = {"X-TBA-App-Id": "frc2067:scouting-system:v02"}
        m = []
        try:
            #get the picture for a given team
            m = self.get("http://www.thebluealliance.com/api/v2/team/frc{0}/media".format(n), params=headers).json()
            if m.status_code == 400:
                m = []
        except:
            pass #swallow the error lol
        for media in m:
            if media['type'] == 'imgur': #check if there's an imgur image on TBA
                imcode = '''<br>
                <div style="text-align: center">
                <p style="font-size: 32px; line-height: 0em;">Image</p>
                <img src=http://i.imgur.com/{}.jpg></img>
                </div>'''.format(media['foreign_key'])
                break
            if media['type'] == 'cdphotothread':
                imcode = '''<br>
                <div style="text-align: center">
                <p style="font-size: 32px; line-height: 0em;">Image</p>
                <img src=http://chiefdelphi.com/media/img/{}></img>
                </div>'''.format(media['details']['image_partial'].replace('_l', '_m'))
                break

        #Every year, update the labels for the graphs. The data will come from the variable dataset
        #Then update all the column headers and stuff
        return '''
        <html>
            <head>
                <title>{0} | PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
                <script type="text/javascript" src="/static/js/amcharts.js"></script>
                <script type="text/javascript" src="/static/js/serial.js"></script>
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
                <script>
                if (typeof jQuery === 'undefined')
                  document.write(unescape('%3Cscript%20src%3D%22/static/js/jquery.js%22%3E%3C/script%3E'));
                </script>
                <script>
                    var chart;
                    var graph;

                    var chartData = {9};

                    AmCharts.ready(function () {{
                        // SERIAL CHART
                        chart = new AmCharts.AmSerialChart();

                        chart.dataProvider = chartData;
                        chart.marginLeft = 10;
                        chart.categoryField = "match";

                        // AXES
                        // category
                        var categoryAxis = chart.categoryAxis;
                        categoryAxis.dashLength = 3;
                        categoryAxis.minorGridEnabled = true;
                        categoryAxis.minorGridAlpha = 0.1;

                        // value
                        var valueAxis = new AmCharts.ValueAxis();
                        valueAxis.position = "left";
                        valueAxis.axisColor = "#111111";
                        valueAxis.gridAlpha = 0;
                        valueAxis.axisThickness = 2;
                        chart.addValueAxis(valueAxis)

                        var valueAxis2 = new AmCharts.ValueAxis();
                        valueAxis2.position = "right";
                        valueAxis2.axisColor = "#FCD202";
                        valueAxis2.gridAlpha = 0;
                        valueAxis2.axisThickness = 2;
                        chart.addValueAxis(valueAxis2);

                        // GRAPH
                        graph = new AmCharts.AmGraph();
                        graph.title = "Auto Shoot Points";
                        graph.valueAxis = valueAxis;
                        graph.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph.lineColor = "#637bb6";
                        graph.bullet = "round";
                        graph.bulletSize = 8;
                        graph.bulletBorderColor = "#FFFFFF";
                        graph.bulletBorderAlpha = 1;
                        graph.bulletBorderThickness = 2;
                        graph.lineThickness = 2;
                        graph.valueField = "autoshoot";
                        graph.balloonText = "Auto Shoot Points:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph);

                        graph2 = new AmCharts.AmGraph();
                        graph2.title = "Auto Gears";
                        graph2.valueAxis = valueAxis2;
                        graph2.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph2.lineColor = "#187a2e";
                        graph2.bullet = "round";
                        graph2.bulletSize = 8;
                        graph2.bulletBorderColor = "#FFFFFF";
                        graph2.bulletBorderAlpha = 1;
                        graph2.bulletBorderThickness = 2;
                        graph2.lineThickness = 2;
                        graph2.valueField = "autogears";
                        graph2.balloonText = "Auto Gears:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph2);

                        graph3 = new AmCharts.AmGraph();
                        graph3.title = "Shoot Points";
                        graph3.valueAxis = valueAxis;
                        graph3.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph3.lineColor = "#FF6600";
                        graph3.bullet = "round";
                        graph3.bulletSize = 8;
                        graph3.bulletBorderColor = "#FFFFFF";
                        graph3.bulletBorderAlpha = 1;
                        graph3.bulletBorderThickness = 2;
                        graph3.lineThickness = 2;
                        graph3.valueField = "shoot";
                        graph3.balloonText = "Shoot Points:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph3);

                        graph4 = new AmCharts.AmGraph();
                        graph4.valueAxis = valueAxis2;
                        graph4.title = "Gears";
                        graph4.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph4.lineColor = "#FCD202";
                        graph4.bullet = "round";
                        graph4.bulletSize = 8;
                        graph4.bulletBorderColor = "#FFFFFF";
                        graph4.bulletBorderAlpha = 1;
                        graph4.bulletBorderThickness = 2;
                        graph4.lineThickness = 2;
                        graph4.valueField = "gears";
                        graph4.balloonText = "Gears:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph4);

                        graph5 = new AmCharts.AmGraph();
                        graph5.valueAxis = valueAxis2;
                        graph5.title = "Dropped Gears";
                        graph5.type = "smoothedLine"; // this line makes the graph smoothed line.
                        graph5.lineColor = "#FF0000";
                        graph5.bullet = "round";
                        graph5.bulletSize = 8;
                        graph5.bulletBorderColor = "#FFFFFF";
                        graph5.bulletBorderAlpha = 1;
                        graph5.bulletBorderThickness = 2;
                        graph5.lineThickness = 2;
                        graph5.valueField = "geardrop";
                        graph5.balloonText = "Dropped Gears:<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                        chart.addGraph(graph5);
                        
                        // CURSOR
                        var chartCursor = new AmCharts.ChartCursor();
                        chartCursor.cursorAlpha = 0;
                        chartCursor.cursorPosition = "mouse";
                        chart.addChartCursor(chartCursor);

                        var legend = new AmCharts.AmLegend();
                        legend.marginLeft = 110;
                        legend.useGraphSettings = true;
                        chart.addLegend(legend);
                        chart.creditsPosition = "bottom-right";

                        // WRITE
                        chart.write("chartdiv");
                    }});

                    function flag(m, f)
                    {{
                        $.post(
                            "flag",
                            {{num: {0}, match: m, flagval: f}},
                            function(data) {{window.location.reload(true);}}
                        );
                    }}
                </script>
            </head>
            <body>
                <h1 class="big">Team {0}</h1>
                <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                <br><br>
                <div style="text-align:center;">
                    <div id="apr">
                        <p style="font-size: 200%; margin: 0.65em; line-height: 0.1em">APR</p>
                        <p style="font-size: 400%; line-height: 0em">{2}</p>
                    </div>
                    <div id="stats">
                        <p class="statbox" style="font-weight:bold">Average match:</p>
                        <p class="statbox">Auto Gears: {3}</p>
                        <p class="statbox">Teleop Gears: {4}</p>
                        <p class="statbox">Dropped Gears: {5}</p>
                        <p class="statbox">Auto Shoot Points: {6}</p>
                        <p class="statbox">Teleop Shoot Points: {7}</p>
                        <p class="statbox">Endgame Points: {8}</p>
                    </div>
                </div>
                <br>
                <div id="chartdiv" style="width:1000px; height:400px; margin: 0 auto;"></div>
                <br>
                <table>
                    <thead><tr>
                        <th>Match</th>
                        <th>Auto</th>
                        <th>Gears</th>
                        <th>Shooting</th>
                        <th>Other</th>
                        <th>Flag</th>
                        <th>Edit</th>
                    </tr></thead>{1}
                </table>
                {10}
                <br>
                <div style="text-align: center; max-width: 700px; margin: 0 auto;">
                    <p style="font-size: 32px; line-height: 0em;">Comments</p>
                    {11}
                    <form style="width: 100%; max-width: 700px;" method="post" action="submit">
                        <input name="team" value="{0}" hidden/>
                        <textarea name="comment" rows="3"></textarea>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                </div>
                <br>
                <p style="text-align: center; font-size: 24px"><a href="/matches?n={0}">View this team's match schedule</a></p>
            </body>
        </html>'''.format(n, output, s[1], s[2], s[3], s[4], s[5], s[6], s[7], str(dataset).replace("'",'"'), imcode, commentstr)

    # Called to flag a data entry
    @cherrypy.expose()
    def flag(self, num='', match='', flagval=0):
        if not (num.isdigit() and match.isdigit()):
            return '<img src="http://goo.gl/eAs7JZ" style="width: 1200px"></img>'
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        cursor.execute('UPDATE scout SET flag=? WHERE d0=? AND d1=?', (int(not int(flagval)),num,match))
        conn.commit()
        conn.close()
        self.calcavg(num, self.getevent())
        self.calcmaxes(num, self.getevent())
        self.calcavgNoD(num, self.getevent())
        self.calcavgLastThree(num, self.getevent())
        return ''
    
    #Called to recalculate all averages/maxes
    @cherrypy.expose()
    def recalculate(self):
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        data = conn.cursor().execute('SELECT * FROM averages ORDER BY apr DESC').fetchall()
        for team in data:
            self.calcavg(team[0], self.getevent())
            self.calcmaxes(team[0], self.getevent())
            self.calcavgNoD(team[0], self.getevent())
            self.calcavgLastThree(team[0], self.getevent())
        return '''
        <html>
            <head>
                <title>PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
            </head>
            <body>
                <h1><a style="color: #B20000" href='/'>PiScout Database</a></h1>
                Recalc Complete
            </body>
        </html>'''
        

    # Input interface to compare teams or alliances
    # This probably won't ever need to be modified
    @cherrypy.expose()
    def compare(self, t='team'):
        return      '''
        <html>
            <head>
                <title>PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
            </head>
            <body>
                <h1 class="big">Compare {0}s</h1>
                <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                <br><br>
                {1}
        </html>'''.format(t.capitalize(), '''
                <p class="main">Enter up to 4 teams</p>
                <form method="get" action="teams">
                    <input class="field" type="text" maxlength="4" name="n1" autocomplete="off"/>
                    <input class="field" type="text" maxlength="4" name="n2" autocomplete="off"/>
                    <input class="field" type="text" maxlength="4" name="n3" autocomplete="off"/>
                    <input class="field" type="text" maxlength="4" name="n4" autocomplete="off"/>
                    <button class="submit" type="submit">Submit</button>
                </form>
        ''' if t=='team' else '''
                <p class="main">Enter two alliances</p>
                <form method="get" action="alliances" style="text-align: center; width: 800px; margin: 0 auto;">
                    <div style="display: table;">
                        <div style="display:table-cell;">
                            <input class="field" type="text" maxlength="4" name="b1" autocomplete="off"/>
                            <input class="field" type="text" maxlength="4" name="b2" autocomplete="off"/>
                            <input class="field" type="text" maxlength="4" name="b3" autocomplete="off"/>
                        </div>
                        <div style="display:table-cell;">
                            <p style="font-size: 64px; line-height: 2.4em;">vs</p>
                        </div>
                        <div style="display:table-cell;">
                            <input class="field" type="text" maxlength="4" name="r1" autocomplete="off"/>
                            <input class="field" type="text" maxlength="4" name="r2" autocomplete="off"/>
                            <input class="field" type="text" maxlength="4" name="r3" autocomplete="off"/>
                        </div>
                    </div>
                    <button class="submit" type="submit">Submit</button>
                </form>''')

    # Output for team comparison
    @cherrypy.expose()
    def teams(self, n1='', n2='', n3='', n4='', stat1='', stat2=''):
        nums = [n1, n2, n3, n4]
        if stat2 == 'none':
            stat2 = ''      
        if not stat1:
            stat1 = 'autogears'
            
        averages = []
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        output = ''
        for n in nums:
            if not n:
                continue
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "You fool! Enter NUMBERS, not letters.")
            average = cursor.execute('SELECT * FROM averages WHERE team=?', (n,)).fetchall()
            assert len(average) < 2
            if len(average):
                entry = average[0]
            else:
                entry = [0]*7
            # Add a data entry for each team
            output += '''<div style="text-align:center; display: inline-block; margin: 16px;">
                            <p><a href="/team?n={0}" style="font-size: 32px; line-height: 0em;">Team {0}</a></p>
                            <div id="apr">
                                <p style="font-size: 200%; margin: 0.65em; line-height: 0.1em">APR</p>
                                <p style="font-size: 400%; line-height: 0em">{1}</p>
                            </div>
                    <div id="stats">
                        <p class="statbox" style="font-weight:bold">Average match:</p>
                        <p class="statbox">Auto Gears: {2}</p>
                        <p class="statbox">Teleop Gears: {3}</p>
                        <p class="statbox">Dropped Gears: {4}</p>
                        <p class="statbox">Auto Shoot Points: {5}</p>
                        <p class="statbox">Teleop Shoot Points: {6}</p>
                        <p class="statbox">Endgame Points: {7}</p>
                    </div>
                        </div>'''.format(n, *entry[1:]) #unpack the elements
        
        teamCharts = ''
        dataset = []
        colors = ["#FF0000", "#000FFF", "#1DD300", "#C100E3", "#AF0000", "#000666", "#0D5B000", "#610172"]
        for idx, n in enumerate(nums):
            if not n:
                continue
            entries = cursor.execute('SELECT * FROM scout WHERE d0=? ORDER BY d1 ASC', (n,)).fetchall()

            for index, e in enumerate(entries):
            # Important: the index of e refers to the number of the field set in main.py
                # For example e[1] gets value #1 from main.py
                dp = {"autoshoot":0, "shoot":0, "autogears":0, "gears":0, "geardrop":0}
                a = ''
                a += 'baseline, ' if e[6] else ''
                a += str(e[5]) + 'x gears, ' if e[5] else ''
                dp['autogears'] += e[5]
                a += str(e[7]) + 'x low goal, ' if e[7] else ''
                a += str(e[8]) + 'x high goal, ' if e[8] else ''
                dp['autoshoot'] += e[7]/3 + e[8]
    
                d = ''
                d += str(e[13]) + 'x gears, ' if e[13] else ''
                d += str(e[14]) + 'x gears dropped, ' if e[14] else ''
                dp['gears'] += e[13]
                dp['geardrop'] += e[14]
    
                sh = ''
                sh += str(e[15]) + 'x low goal, ' if e[15] else ''
                sh += str(e[16]) + 'x high goal, ' if e[16] else ''
                dp['shoot'] += e[15]/9 + e[16]/3
    
                o = 'hang, ' if e[17] else 'failed hang, ' if e[18] else ''
                o += str(e[3]) + 'x foul, ' if e[3] else ''
                o += str(e[4]) + 'x tech foul, ' if e[4] else ''
                o += 'defense, ' if e[11] else ''
                o += 'feeder, ' if e[10] else ''
                o += 'defended, ' if e[12] else ''
                for key,val in dp.items():
                    dp[key] = round(val, 2)
                if not e[19]:
                    if len(dataset) < (index + 1):
                        if stat2:
                            dataPoint = {"match":(index+1), "team" + n + "stat1":dp[stat1], "team" + n + "stat2":dp[stat2]}
                        else:
                            dataPoint = {"match":(index+1), "team" + n + "stat1":dp[stat1]}
                        dataset.append(dataPoint)
                    else:
                        dataset[index]["team" + n + "stat1"] = dp[stat1]
                        if stat2:
                            dataset[index]["team" + n + "stat2"] = dp[stat2]

            teamCharts += '''// GRAPH
                            graph{0} = new AmCharts.AmGraph();
                            graph{0}.title = "{1}";
                            graph{0}.valueAxis = valueAxis;
                            graph{0}.type = "smoothedLine"; // this line makes the graph smoothed line.
                            graph{0}.lineColor = "{3}";
                            graph{0}.bullet = "round";
                            graph{0}.bulletSize = 8;
                            graph{0}.bulletBorderColor = "#FFFFFF";
                            graph{0}.bulletBorderAlpha = 1;
                            graph{0}.bulletBorderThickness = 2;
                            graph{0}.lineThickness = 2;
                            graph{0}.valueField = "{2}";
                            graph{0}.balloonText = "{1}<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                            chart.addGraph(graph{0});
                            '''.format(n + "_1", "Team " + n + stat1, "team" + n + "stat1", colors[idx])
            if stat2:
                teamCharts += '''// GRAPH
                graph{0} = new AmCharts.AmGraph();
                graph{0}.title = "{1}";
                graph{0}.valueAxis = valueAxis2;
                graph{0}.type = "smoothedLine"; // this line makes the graph smoothed line.
                graph{0}.lineColor = "{3}";
                graph{0}.bullet = "round";
                graph{0}.bulletSize = 8;
                graph{0}.bulletBorderColor = "#FFFFFF";
                graph{0}.bulletBorderAlpha = 1;
                graph{0}.bulletBorderThickness = 2;
                graph{0}.lineThickness = 2;
                graph{0}.valueField = "{2}";
                graph{0}.balloonText = "{1}<br><b><span style='font-size:14px;'>[[value]]</span></b>";
                chart.addGraph(graph{0});
                '''.format(n + "_2", "Team " + n + stat2, "team" + n + "stat2", colors[4+idx])
        chart = '''
                <script>
                    var chart;
                    var graph;

                    var chartData = {1};

                    AmCharts.ready(function () {{
                        // SERIAL CHART
                        chart = new AmCharts.AmSerialChart();

                        chart.dataProvider = chartData;
                        chart.marginLeft = 10;
                        chart.categoryField = "match";

                        // AXES
                        // category
                        var categoryAxis = chart.categoryAxis;
                        categoryAxis.dashLength = 3;
                        categoryAxis.minorGridEnabled = true;
                        categoryAxis.minorGridAlpha = 0.1;

                        // value
                        var valueAxis = new AmCharts.ValueAxis();
                        valueAxis.position = "left";
                        valueAxis.axisColor = "#111111";
                        valueAxis.gridAlpha = 0;
                        valueAxis.axisThickness = 2;
                        chart.addValueAxis(valueAxis)

                        var valueAxis2 = new AmCharts.ValueAxis();
                        valueAxis2.position = "right";
                        valueAxis2.axisColor = "#FCD202";
                        valueAxis2.gridAlpha = 0;
                        valueAxis2.axisThickness = 2;
                        chart.addValueAxis(valueAxis2);
                        
                        {0}
                        
                        // CURSOR
                        var chartCursor = new AmCharts.ChartCursor();
                        chartCursor.cursorAlpha = 0;
                        chartCursor.cursorPosition = "mouse";
                        chart.addChartCursor(chartCursor);

                        var legend = new AmCharts.AmLegend();
                        legend.marginLeft = 110;
                        legend.useGraphSettings = true;
                        chart.addLegend(legend);
                        chart.creditsPosition = "bottom-right";

                        // WRITE
                        chart.write("chartdiv");
                    }});
                $(document).ready(function() {{
                    $("#{2}").attr("selected", "selected");
                    $("#{3}").attr("selected", "selected");
                }});
                </script>
            '''.format(teamCharts, str(dataset).replace("'",'"'), stat1, stat2 + "2")

        return '''
        <html>
            <head>
                <title>PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
                <script type="text/javascript" src="/static/js/amcharts.js"></script>
                <script type="text/javascript" src="/static/js/serial.js"></script>
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
                <script>
                if (typeof jQuery === 'undefined')
                  document.write(unescape('%3Cscript%20src%3D%22/static/js/jquery.js%22%3E%3C/script%3E'));
                </script>
                {1}
            </head>
            <body>
                <h1 class="big">Compare Teams</h1>
                <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                <br><br>
                <div style="margin: 0 auto; text-align: center; max-width: 900px;">
                {0}
                <br><br><br>
                </div>
                <div id="chartdiv" style="width:1000px; height:400px; margin: 0 auto;"></div>
                <div id="statSelect" style="width:600px; margin:auto;">
                    <form method="post" action="" style="float:left">
                            <select class="fieldsm" name="stat1">
                              <option id="autoshoot" value="autoshoot">Auto Shoot Points</option>
                              <option id="autogears" value="autogears">Auto Gears</option>
                              <option id="shoot" value="shoot">Teleop Shoot Points</option>
                              <option id="gears" value="gears">Teleop Gears</option>
                              <option id="geardrop" value="geardrop">Dropped Gears</option>
                            </select>
                            <button class="submit" type="submit">Submit</button>
                    </form>
                    <form method="post" action="" style="float:right">
                            <select class="fieldsm" name="stat2">
                                <option id="none" value="none">None</option>
                                <option id="autoshoot2" value="autoshoot">Auto Shoot Points</option>
                                <option id="autogears2" value="autogears">Auto Gears</option>
                                <option id="shoot2" value="shoot">Teleop Shoot Points</option>
                                <option id="gears2" value="gears">Teleop Gears</option>
                                <option id="geardrop2" value="geardrop">Dropped Gears</option>
                            </select>
                            <button class="submit" type="submit">Submit</button>
                    </form>
                </div>
            </body>
        </html>'''.format(output, chart)

    # Output for alliance comparison
    @cherrypy.expose()
    def alliances(self, b1='', b2='', b3='', r1='', r2='', r3='', mode='', level=''):
        if mode == '':
            mode = 'averages'
        if level == '':
            level = 'quals'
        nums = [b1, b2, b3, r1, r2, r3]
        averages = []
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        #start a div table for the comparison
        #to later be formatted with sum APR
        output = '''<div style="display: table">
                        <div style="display: table-cell;">
                        <p style="font-size: 36px; color: #0000B8; line-height: 0;">Blue Alliance</p>
                    <p style="font-size: 24px; color: #0000B8; line-height: 0.2;">{2}% chance of win</p>
                        <div id="apr" style="width:185px">
                            <p style="font-size: 200%; margin: 0.65em; line-height: 0.1em">Proj. Score</p>
                            <p style="font-size: 400%; line-height: 0em">{0}</p>
                            <br>
                        </div>'''
        ballScore = []
        endGame = []
        autoGears = []
        teleopGears = []
        #iterate through all six teams
        color = "#0000B8"
        for i,n in enumerate(nums):
            #at halfway point switch to the second row
            if i == 3:
                output+='''</div>
                        <div style="display: table-cell;">
                        <p style="font-size: 36px; color: #B20000; line-height: 0;">Red Alliance</p>
                        <p style="font-size: 24px; color: #B20000; line-height: 0.2;">{3}% chance of win</p>
                        <div id="apr" style="width:185px">
                            <p style="font-size: 200%; margin: 0.65em; line-height: 0.1em">Proj. Score</p>
                            <p style="font-size: 400%; line-height: 0em">{1}</p>
                            <br>
                        </div>'''
                color = "#B20000"
            if not n.isdigit():
                raise cherrypy.HTTPError(400, "You fool! Enter six valid team numbers!")
            if mode == 'averages':
                average = cursor.execute('SELECT * FROM averages WHERE team=?', (n,)).fetchall()
            else:
                average = cursor.execute('SELECT * FROM maxes WHERE team=?', (n,)).fetchall()
            assert len(average) < 2
            if len(average):
                entry = average[0]
            else:
                entry = [0]*8
            output += '''<div style="text-align:center; display: inline-block; margin: 16px;">
                            <p><a href="/team?n={0}" style="font-size: 32px; line-height: 0em; color: {8} !important">Team {0}</a></p>
                            <div id="apr">
                                <p style="font-size: 200%; margin: 0.65em; line-height: 0.1em">APR</p>
                                <p style="font-size: 400%; line-height: 0em">{1}</p>
                            </div>
                            <div id="stats">
                                <p class="statbox" style="font-weight:bold">Average match:</p>
                                <p class="statbox">Auto Gears: {2}</p>
                                <p class="statbox">Teleop Gears: {3}</p>
                                <p class="statbox">Dropped Gears: {4}</p>
                                <p class="statbox">Auto Shoot Points: {5}</p>
                                <p class="statbox">Teleop Shoot Points: {6}</p>
                                <p class="statbox">Endgame Points: {7}</p>
                            </div>
                        </div>'''.format(n, *entry[1:], color) #unpack the elements
        output += "</div></div>"
        
        blue_score = self.predictScore(nums[0:3], level)['score']
        red_score = self.predictScore(nums[3:], level)['score']
        blue_score = int(blue_score)
        red_score = int(red_score)
        
        prob_red = 1/(1+math.e**(-0.08099*(red_score - blue_score))) #calculates win probability from 2016 data
        output = output.format(blue_score, red_score, round((1-prob_red)*100,1), round(prob_red*100,1))
        conn.close()

        return '''
        <html>
            <head>
                <title>PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
                <script>
                if (typeof jQuery === 'undefined')
                  document.write(unescape('%3Cscript%20src%3D%22/static/js/jquery.js%22%3E%3C/script%3E'));
                </script>
                <script>
                    $(document).ready(function() {{
                        $("#{1}").attr("selected", "selected");
                        $("#{2}").attr("selected", "selected");
                    }});
                </script>
            </head>
            <body>
                <h1 class="big">Compare Alliances</h1>
                <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                <div id="statSelect" class="no-print" style="width:600px; margin:auto;">
                    <form method="post" action="" style="float:left">
                            <select class="fieldsm" name="mode">
                              <option id="averages" value="averages">Averages</option>
                              <option id="maxes" value="maxes">Maxes</option>
                            </select>
                            <button class="submit" type="submit">Submit</button>
                    </form>
                    <form method="post" action="" style="float:right">
                            <select class="fieldsm" name="level">
                                <option id="quals" value="quals">Qualifications</option>
                                <option id="playoffs" value="playoffs">Playoffs</option>
                            </select>
                            <button class="submit" type="submit">Submit</button>
                    </form>
                </div>
                <div style="margin: 0 auto; text-align: center; max-width: 1000px;">
                {0}
                </div>
            </body>
        </html>'''.format(output, mode, level)

    # Lists schedule data from TBA
    @cherrypy.expose()
    def matches(self, n=0):
        n = int(n)
        event = self.getevent()
        datapath = 'data_' + event + '.db'
        self.database_exists(event)
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        
        m = self.getMatches(event, n)

        output = ''

        if 'feed' in m:
            raise cherrypy.HTTPError(503, "Unable to retrieve data about this event.")
        
        #assign weights, so we can sort the matches
        for match in m:
            match['value'] = match['match_number']
            type = match['comp_level']
            if type == 'qf':
                match['value'] += 1000
            elif type == 'sf':
                match['value'] += 2000
            elif type == 'f':
                match['value'] += 3000

        m = sorted(m, key=lambda k: k['value'])
        for match in m:
            if match['comp_level'] != 'qm':
                match['num'] = match['comp_level'].upper() + ' ' + str(match['match_number'])
            else:
                match['num'] = match['match_number']
            output += '''
            <tr>
                <td><a href="alliances?b1={1}&b2={2}&b3={3}&r1={4}&r2={5}&r3={6}">{0}</a></td>
                <td><a href="team?n={1}">{1}</a></td>
                <td><a href="team?n={2}">{2}</a></td>
                <td><a href="team?n={3}">{3}</a></td>
                <td><a href="team?n={4}">{4}</a></td>
                <td><a href="team?n={5}">{5}</a></td>
                <td><a href="team?n={6}">{6}</a></td>
                <td>{7}</td>
                <td>{8}</td>
            </tr>
            '''.format(match['num'], match['alliances']['blue']['teams'][0][3:],
                        match['alliances']['blue']['teams'][1][3:], match['alliances']['blue']['teams'][2][3:],
                        match['alliances']['red']['teams'][0][3:], match['alliances']['red']['teams'][1][3:],
                        match['alliances']['red']['teams'][2][3:], match['alliances']['blue']['score'],
                        match['alliances']['red']['score'])

        return '''
            <html>
            <head>
                <title>PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
            </head>
            <body>
                <h1>Matches{0}</h1>
                <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                <br><br>
                <table>
                <thead><tr>
                    <th>Match</th>
                    <th>Blue 1</th>
                    <th>Blue 2</th>
                    <th>Blue 3</th>
                    <th>Red 1</th>
                    <th>Red 2</th>
                    <th>Red 3</th>
                    <th>Blue Score</th>
                    <th>Red Score</th>
                </tr></thead>
                <tbody>
                {1}
                </tbody>
                </table>
            </body>
            </html>
        '''.format(": {}".format(n) if n else "", output)

    # Used by the scanning program to submit data, and used by comment system to submit data
    # this won't ever need to change
    @cherrypy.expose()
    def submit(self, data='', event='', team='', comment=''):
        if not (data or team):
            return '''
                <h1>FATAL ERROR</h1>
                <h3>DATA CORRUPTION</h3>
                <p>Erasing database to prevent further damage to the system.</p>'''

        if data == 'json':
            return '[]' #bogus json for local version

        datapath = 'data_' + event + '.db'
        self.database_exists(event)
        conn = sql.connect(datapath)
        cursor = conn.cursor()

        if team:
            if not comment:
                conn.close()
                raise cherrypy.HTTPRedirect('/team?n=' + str(team))
            cursor.execute('INSERT INTO comments VALUES (?, ?)', (team, comment))
            conn.commit()
            conn.close()
            raise cherrypy.HTTPRedirect('/team?n=' + str(team))

        d = literal_eval(data)
        flag = 0
        if (d[6] or d[14]) and (d[7] or d[15]): #high and low balls
            flag = 1
        if d[16] and d[17]:
            flag = 1
            
        m = self.getMatches(event)
                
        if m:
            match = next((item for item in m if (item['match_number'] == d[1]) and (item['comp_level'] == 'qm')))
            teams = match['alliances']['blue']['teams'] + match['alliances']['red']['teams']
            if not 'frc' + str(d[0]) in teams:
                flag = 1   
                
        if d[4]:    #if auto gear, set baseline
            d[5] = 1
            
        if d[18]:   #replay
            cursor.execute('DELETE from scout WHERE d0=? AND d1=?', (str(d[0]),str(d[1])))
        d = d[:18] + d[19:]
        cursor.execute('INSERT INTO scout VALUES (NULL,' + ','.join([str(a) for a in d])  + ',' + str(flag) + ')')
        conn.commit()
        conn.close()

        self.calcavg(d[0], event)
        self.calcmaxes(d[0], event)
        self.calcavgNoD(d[0], event)
        self.calcavgLastThree(d[0], event)
        return ''

    # Calculates average scores for a team
    def calcavg(self, n, event):
        datapath = 'data_' + event + '.db'
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        #delete the existing entry, if a team has no matches they will be removed
        cursor.execute('DELETE FROM averages WHERE team=?',(n,))
        #d0 is the identifier for team, d1 is the identifier for match
        entries = cursor.execute('SELECT * FROM scout WHERE d0=? AND flag=0 ORDER BY d1 DESC', (n,)).fetchall()
        s = {'autogears': 0, 'teleopgears': 0, 'geardrop': 0, 'autoballs': 0, 'teleopballs':0, 'end': 0, 'defense': 0}
        apr = 0
        # Iterate through all entries (if any exist) and sum all categories
        if entries:
            for e in entries:
                e = e[1:]
                s['autogears'] += e[4]
                s['teleopgears'] += e[12]
                s['autoballs'] += e[6]/3 + e[7]
                s['teleopballs'] += e[14]/9 + e[15]/3
                s['geardrop'] += e[13]
                s['end'] += e[16]*50
                s['defense'] += e[10]

            # take the average (divide by number of entries)
            for key,val in s.items():
                s[key] = round(val/len(entries), 2)

            # formula for calculating APR (point contribution)
            apr = s['autoballs'] + s['teleopballs'] + s['end']
            if s['autogears']:
                apr += 20 * min(s['autogears'], 1)
            if s['autogears'] > 1:
                apr += (s['autogears'] - 1) * 10   
                
            apr += max(min(s['teleopgears'], 2 - s['autogears']) * 20, 0)
            if s['autogears'] + s['teleopgears'] > 2:
                apr += min(s['teleopgears'] + s['autogears'] - 2, 4) * 10
            if s['autogears'] + s['teleopgears'] > 6:
                apr += min(s['teleopgears'] + s['autogears'] - 6, 6) * 7
            apr = int(apr)

            #replace the data entry with a new one
            cursor.execute('INSERT INTO averages VALUES (?,?,?,?,?,?,?,?,?)',(n, apr, s['autogears'], s['teleopgears'], s['geardrop'], s['autoballs'], s['teleopballs'], s['end'], s['defense']))
        conn.commit()
        conn.close()
        
        # Calculates average scores for a team
    def calcavgNoD(self, n, event):
        datapath = 'data_' + event + '.db'
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        #delete the existing entry, if a team has no matches they will be removed
        cursor.execute('DELETE FROM noDefense WHERE team=?',(n,))
        #d0 is the identifier for team, d1 is the identifier for match
        entries = cursor.execute('SELECT * FROM scout WHERE d0=? AND flag=0 AND d10=0 ORDER BY d1 DESC', (n,)).fetchall()
        s = {'autogears': 0, 'teleopgears': 0, 'geardrop': 0, 'autoballs': 0, 'teleopballs':0, 'end': 0, 'defense': 0}
        apr = 0
        # Iterate through all entries (if any exist) and sum all categories
        if entries:
            for e in entries:
                e = e[1:]
                s['autogears'] += e[4]
                s['teleopgears'] += e[12]
                s['autoballs'] += e[6]/3 + e[7]
                s['teleopballs'] += e[14]/9 + e[15]/3
                s['geardrop'] += e[13]
                s['end'] += e[16]*50
                s['defense'] += e[10]

            # take the average (divide by number of entries)
            for key,val in s.items():
                s[key] = round(val/len(entries), 2)

            # formula for calculating APR (point contribution)
            apr = s['autoballs'] + s['teleopballs'] + s['end']
            if s['autogears']:
                apr += 20 * min(s['autogears'], 1)
            if s['autogears'] > 1:
                apr += (s['autogears'] - 1) * 10   
                
            apr += max(min(s['teleopgears'], 2 - s['autogears']) * 20, 0)
            if s['autogears'] + s['teleopgears'] > 2:
                apr += min(s['teleopgears'] + s['autogears'] - 2, 4) * 10
            if s['autogears'] + s['teleopgears'] > 6:
                apr += min(s['teleopgears'] + s['autogears'] - 6, 6) * 7
            apr = int(apr)

            #replace the data entry with a new one
            cursor.execute('INSERT INTO noDefense VALUES (?,?,?,?,?,?,?,?,?)',(n, apr, s['autogears'], s['teleopgears'], s['geardrop'], s['autoballs'], s['teleopballs'], s['end'], s['defense']))
        conn.commit()
        conn.close()
        
    # Calculates average scores for a team
    def calcavgLastThree(self, n, event):
        datapath = 'data_' + event + '.db'
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        #delete the existing entry, if a team has no matches they will be removed
        cursor.execute('DELETE FROM lastThree WHERE team=?',(n,))
        #d0 is the identifier for team, d1 is the identifier for match
        entries = cursor.execute('SELECT * FROM scout WHERE d0=? AND flag=0 ORDER BY d1 DESC', (n,)).fetchall()
        s = {'autogears': 0, 'teleopgears': 0, 'geardrop': 0, 'autoballs': 0, 'teleopballs':0, 'end': 0, 'defense': 0}
        apr = 0
        # Iterate through all entries (if any exist) and sum all categories
        if entries:
            entries = entries[0:3]
            for e in entries:
                e = e[1:]
                s['autogears'] += e[4]
                s['teleopgears'] += e[12]
                s['autoballs'] += e[6]/3 + e[7]
                s['teleopballs'] += e[14]/9 + e[15]/3
                s['geardrop'] += e[13]
                s['end'] += e[16]*50
                s['defense'] += e[10]

            # take the average (divide by number of entries)
            for key,val in s.items():
                s[key] = round(val/len(entries), 2)

            # formula for calculating APR (point contribution)
            apr = s['autoballs'] + s['teleopballs'] + s['end']
            if s['autogears']:
                apr += 20 * min(s['autogears'], 1)
            if s['autogears'] > 1:
                apr += (s['autogears'] - 1) * 10   
                
            apr += max(min(s['teleopgears'], 2 - s['autogears']) * 20, 0)
            if s['autogears'] + s['teleopgears'] > 2:
                apr += min(s['teleopgears'] + s['autogears'] - 2, 4) * 10
            if s['autogears'] + s['teleopgears'] > 6:
                apr += min(s['teleopgears'] + s['autogears'] - 6, 6) * 7
            apr = int(apr)

            #replace the data entry with a new one
            cursor.execute('INSERT INTO lastThree VALUES (?,?,?,?,?,?,?,?,?)',(n, apr, s['autogears'], s['teleopgears'], s['geardrop'], s['autoballs'], s['teleopballs'], s['end'], s['defense']))
        conn.commit()
        conn.close()
        
    def calcmaxes(self, n, event):
        datapath = 'data_' + event + '.db'
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        
        #delete entry, if the team has match records left it will be replaced later
        cursor.execute('DELETE FROM maxes WHERE team=?',(n,))
        entries = cursor.execute('SELECT * FROM scout WHERE d0 = ? AND flag=0 ORDER BY d1 DESC',(n,)).fetchall()
        s = {'autogears': 0, 'teleopgears': 0, 'geardrop': 0, 'autoballs': 0, 'teleopballs':0, 'end': 0, 'apr':0, 'defense': 0 }
        apr = 0
        # Iterate through all entries (if any exist) and sum all categories
        if entries:
            for e in entries:
                e = e[1:]
                s['autogears'] = max(s['autogears'], e[4])
                s['teleopgears'] = max(s['teleopgears'], e[12])
                s['autoballs'] = max(s['autoballs'], (e[6]/3 + e[7]))
                s['teleopballs'] = max(s['teleopballs'], (e[14]/9 + e[15]/3))
                s['geardrop'] = max(s['geardrop'], e[13])
                s['end'] = max(s['end'], e[16]*50)
                s['defense'] = max(s['defense'], e[11])
                apr = (e[6]/3 + e[7]) + (e[14]/9 + e[15]/3) + e[16]*50
                if e[4]:
                    apr += 60
                if e[4] > 1:
                    apr += (e[4] - 1) * 30   
                    
                apr += min(min(e[12], 2 - e[4]) * 20, 0)
                if e[4] + e[12] > 2:
                    apr += min(e[12] + e[4] - 2, 4) * 10
                if e[4] + e[12] > 6:
                    apr += min(e[12] + e[4] - 6, 6) * 7
                s['apr'] = max(s['apr'], (int(apr)))

        for key,val in s.items():
            s[key] = round(val, 2)
        #replace the data entry with a new one

        cursor.execute('INSERT INTO maxes VALUES (?,?,?,?,?,?,?,?,?)',(n, s['apr'], s['autogears'], s['teleopgears'], s['geardrop'], s['autoballs'], s['teleopballs'], s['end'], s['defense']))
        conn.commit()
        conn.close()

    # Return the path to the database for this event
    def datapath(self):
        return 'data_' + self.getevent() + '.db'

    # Return the selected event
    def getevent(self):
        if 'event' not in cherrypy.session:
            cherrypy.session['event'] = CURRENT_EVENT
        return cherrypy.session['event']
    
    def getMatches(self, event, team=''):
        headers = {"X-TBA-App-Id": "frc2067:scouting-system:v02"}
        try:
            if team:
                #request a specific team
                m = requests.get("http://www.thebluealliance.com/api/v2/team/frc{0}/event/{1}/matches".format(team, event), params=headers)
            else:
                #get all the matches from this event
                m = requests.get("http://www.thebluealliance.com/api/v2/event/{0}/matches".format(event), params=headers)
            if m.status_code == 400 or m.status_code == 404:
                raise Exception
            if m.text != '[]':
                with open(event + "_matches.json", "w+") as file:
                    file.write(str(m.text))
                m = m.json()
            else:
                m = []
        except:
            try:
                with open(event + '_matches.json') as matches_data:
                    m = json.load(matches_data)
            except:
                m = []
        return m

    # Wrapper for requests, ensuring nothing goes terribly wrong
    # This code is trash; it just works to avoid errors when running without internet
    def get(self, req, params=""):
        a = None
        try:
            a = requests.get(req, params=params)
            if a.status_code == 404:
                raise Exception #freaking stupid laziness
        except:
            #stupid lazy solution for local mode
            a = requests.get('http://127.0.0.1:8000/submit?data=json')
        return a
    
    def database_exists(self, event):
        datapath = 'data_' + event + '.db'
        if not os.path.isfile(datapath):
            # Generate a new database with the three tables
            conn = sql.connect(datapath)
            cursor = conn.cursor()
            # Replace 36 with the number of entries in main.py
            cursor.execute('CREATE TABLE scout (key INTEGER PRIMARY KEY,' + ','.join([('d' + str(a) + ' integer') for a in range (22)]) + ',flag integer' + ')')
            cursor.execute('''CREATE TABLE averages (team integer,apr integer,autogear real,teleopgear real, geardrop real, autoballs real, teleopballs real, end real)''')
            cursor.execute('''CREATE TABLE maxes (team integer, apr integer, autogear real, teleopgear real, geardrop real, autoballs real, teleopballs real, end real)''')
            cursor.execute('''CREATE TABLE comments (team integer, comment text)''')
            conn.close()
            
    @cherrypy.expose()
    def edit(self, key='', team='', match='', fouls='', techFouls='', autoGears='', autoBaseline='',
             autoLowBalls='', autoHighBalls='', gearsFloor='', feeder='', defense='', defended='',
             teleGears='', teleGearsDropped='', teleLowBalls='', teleHighBalls='', hang='', failHang='', flag=''):
        datapath = 'data_' + self.getevent() + '.db'
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        if team:
            data = (team, match, fouls, techFouls, autoGears, autoBaseline, autoLowBalls, autoHighBalls,
                    gearsFloor, feeder, defense, defended, teleGears, teleGearsDropped, teleLowBalls,
                    teleHighBalls, hang, failHang)
            sqlCommand = 'UPDATE scout SET '
            for index, item in enumerate(data):
                if item:
                    if item == 'on':
                        sqlCommand+= 'd' + str(index) + '=1,'
                    else:
                        sqlCommand+= 'd' + str(index) + '=' + str(item) + ','
                else:
                    sqlCommand+= 'd' + str(index) + '=0,'
            if flag:
                sqlCommand+='flag=1 '
            else: 
                sqlCommand+='flag=0 '
            sqlCommand+='WHERE key=' + str(key)
            cursor.execute(sqlCommand)
            conn.commit()
            conn.close()
            self.calcavg(team, self.getevent())
            self.calcmaxes(team, self.getevent())
            self.calcavgNoD(team, self.getevent())
            self.calcavgLastThree(team, self.getevent())
        conn = sql.connect(datapath)
        cursor= conn.cursor()
        entries = cursor.execute('SELECT * from scout ORDER BY flag DESC, d0 ASC, d1 ASC').fetchall()
                
        if key == '':
            key = entries[0][0]
        combobox = '''<form method="post" action="edit">
                        <select class="fieldsm" name="key">'''

        for e in entries:
            combobox += '''<option id="{0}" value="{0}">{1} Team {2}: Match {3}</option>\n'''.format(e[0], "*" if e[19] else "", e[1], e[2])
                         
        combobox += '''</select>
                        <button class="submit" type="submit">Submit</button>
                    </form>
                    <br><br>'''
        
        entry = cursor.execute('SELECT * from scout WHERE key=?', (key,)).fetchone()
        conn.close()
        mainEditor = '''<h1>Editing Team {0[1]}: Match {0[2]}</h1>
                        <br>
                        <form method="post" action="edit" style="width:670px">
                                <div class="editHeaderLeft">Match Info</div>
                                <div class="editHeaderRight">Fouls</div>
                                <div class="editCellLeft">
                                    <input type="number" name="key" value="{8}" hidden/>
                                    <label for="team" class="editLabel">Team</label>
                                    <input class="editNum" type="number" name="team" value="{0[1]}">
                                    <br>
                                    <label for="match" class="editLabel">Match</label>
                                    <input class="editNum" type="number" name="match" value="{0[2]}">
                                </div>
                                <div class="editCellRight">
                                    <label for="fouls" class="editLabel">Fouls</label>
                                    <input class="editNum" type="number" name="fouls" value="{0[3]}">
                                    <br>
                                    <label for="techFouls" class="editLabel">Tech Fouls</label>
                                    <input class="editNum" type="number" name="techFouls" value="{0[4]}">
                                </div>
                                <div class="editHeaderLeft">Auto</div>
                                <div class="editHeaderRight">Teleop</div>
                                <div class="editCellLeft">
                                    <label for="autoGears" class="editLabel">Auto Gears</label>
                                    <input class="editNum" type="number" name="autoGears" value="{0[5]}">
                                    <br>
                                    <label for="autoBaseline" class="editLabel">Auto Baseline</label>
                                    <input class="editNum" type="checkbox" name="autoBaseline" {1}>
                                    <br>
                                    <label for="autoLowBalls" class="editLabel">Auto Low Balls</label>
                                    <input class="editNum" type="number" name="autoLowBalls" value="{0[7]}">
                                    </br>
                                    <label for="autoHighBalls" class="editLabel">Auto High Balls</label>
                                    <input class="editNum" type="number" name="autoHighBalls" value="{0[8]}">
                                </div>
                                <div class="editCellRight">
                                    <label for="teleGears" class="editLabel">Teleop Gears</label>
                                    <input class="editNum" type="number" name="teleGears" value="{0[13]}">
                                    <br>
                                    <label for="teleGearsDropped" class="editLabel">Teleop Dropped Gears</label>
                                    <input class="editNum" type="number" name="teleGearsDropped" value="{0[14]}">
                                    <br>
                                    <label for="teleLowBalls" class="editLabel">Teleop Low Balls</label>
                                    <input class="editNum" type="number" name="teleLowBalls" value="{0[15]}">
                                    <br>
                                    <label for="teleHighBalls" class="editLabel">Teleop High Balls</label>
                                    <input class="editNum" type="number" name="teleHighBalls" value="{0[16]}">
                                </div>
                                <div class="editHeaderLeft">Other</div>
                                <div class="editHeaderRight">End Game</div>
                                <div class="editCellLeft">
                                    <label for="gearsFloor" class="editLabel">Gear Floor Intake</label>
                                    <input class="editNum" type="checkbox" name="gearsFloor" {2}>
                                    <br>
                                    <label for="feeder" class="editLabel">Feeder Bot</label>
                                    <input class="editNum" type="checkbox" name="feeder" {3}>
                                    <br>
                                    <label for="defense" class="editLabel">Defense Bot</label>
                                    <input class="editNum" type="checkbox" name="defense" {4}>
                                    <label for="defended" class="editLabel">Defended</label>
                                    <input class="editNum" type="checkbox" name="defended" {5}>
                                    <br>
                                </div>
                                <div class="editCellRight">
                                    <label for="hang" class="editLabel">Hang</label>
                                    <input class="editNum" type="checkbox" name="hang" {6}>
                                    <br>
                                    <label for="failhang" class="editLabel">Failed Hang</label>
                                    <input class="editNum" type="checkbox" name="failHang" {7}>
                                    <br>
                                    <br>
                                    <br>
                                </div>
                                <div class="editHeaderLeft">Flag</div>
                                <div class="editHeaderRight">Submit</div>
                                <div class="editCellLeft">
                                    <label for="flag" class="editLabel">Flagged</label>
                                    <input class="editNum" type="checkbox" name="flag" {9}>
                                </div>
                                <div class="editCellRight">
                                    <input type="submit" value="Submit">
                                </div>
                        </form>'''.format(entry, "checked" if entry[6] else "", "checked" if entry[9] else "",
                                          "checked" if entry[10] else "", "checked" if entry[11] else "",
                                          "checked" if entry[12] else "", "checked" if entry[17] else "",
                                          "checked" if entry[18] else "", key, "checked" if entry[19] else "")
        
        
        return '''
            <html>
            <head>
                <title>PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
                <script>
                $(document).ready(function() {{
                    $("#{0}").attr("selected", "selected");
                }});
                </script>
            </head>
            <body>
                <h1><a style="color: #B20000" href='/'>PiScout</a></h1>
                <h2><syle="colorL #B20000">Match Editor</h2>
                <br><br>
            '''.format(str(key)) + combobox + mainEditor + '''</body>'''
            
    @cherrypy.expose()
    def rankings(self):
        event = self.getevent()
        datapath = 'data_' + event + '.db'
        self.database_exists(event)
        conn = sql.connect(datapath)
        cursor = conn.cursor()
        
        rankings = {}
        
        headers = {"X-TBA-App-Id": "frc2067:scouting-system:v02"}
        m = requests.get("http://www.thebluealliance.com/api/v2/event/{0}/matches".format(event), params=headers)
        r = requests.get("http://www.thebluealliance.com/api/v2/event/{0}/rankings".format(event), params=headers)
        if 'feed' in m:
            raise cherrypy.HTTPError(503, "Unable to retrieve data about this event.")
        if r.text != '[]':
            r = r.json()
        else:
            raise cherrypy.HTTPError(503, "Unable to retrieve rankings data for this event.")
        if m.text != '[]':
            m = m.json()
        else:
            raise cherrypy.HTTPError(503, "Unable to retrieve match data for this event.")
 
        del r[0]
        for item in r:
            rankings[str(item[1])] = {'rp': round(item[2]*item[9],0), 'matchScore': item[3], 'currentRP': round(item[2]*item[9],0), 'currentMatchScore': item[3]}
            
        for match in m:
            if match['comp_level'] == 'qm':
                if match['alliances']['blue']['score'] == -1:
                    blueTeams = [match['alliances']['blue']['teams'][0][3:], match['alliances']['blue']['teams'][1][3:], match['alliances']['blue']['teams'][2][3:]]
                    blueResult = self.predictScore(blueTeams)
                    blueRP = blueResult['fuelRP'] + blueResult['gearRP']
                    redTeams = [match['alliances']['red']['teams'][0][3:], match['alliances']['red']['teams'][1][3:], match['alliances']['red']['teams'][2][3:]]
                    redResult = self.predictScore(redTeams)
                    redRP = redResult['fuelRP'] + redResult['gearRP']
                    if blueResult['score'] > redResult['score']:
                        blueRP += 2
                    elif redResult['score'] > blueResult['score']:
                        redRP += 2
                    else:
                        redRP += 1
                        blueRP += 1
                    for team in blueTeams:
                        rankings[team]['rp'] += blueRP
                        rankings[team]['matchScore'] += blueResult['score']
                    for team in redTeams:
                        rankings[team]['rp'] += redRP
                        rankings[team]['matchScore'] += redResult['score']

        output = ''
        for index,out in enumerate(sorted(rankings.items(), key=keyFromItem(lambda k,v: (v['rp'], v['matchScore'])), reverse=True)):
            output += '''
            <tr>
                <td>{0}</td>
                <td><a href="team?n={1}">{1}</a></td>
                <td>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td>{5}</td>
            </tr>
            '''.format(index + 1, out[0], (int)(out[1]['rp']), (int)(out[1]['matchScore']), (int)(out[1]['currentRP']), (int)(out[1]['currentMatchScore']))
        return '''
            <html>
            <head>
                <title>PiScout</title>
                <link href="http://fonts.googleapis.com/css?family=Chau+Philomene+One" rel="stylesheet" type="text/css">
                <link href="/static/css/style.css" rel="stylesheet">
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
                <script>
                if (typeof jQuery === 'undefined')
                  document.write(unescape('%3Cscript%20src%3D%22/static/js/jquery.js%22%3E%3C/script%3E'));
                </script>
                <script type="text/javascript" src="./static/js/jquery.tablesorter.js"></script>
                <script>
                $(document).ready(function() {{
                    $("table").tablesorter();
                }});
                </script>
            </head>
            <body>
                <h1>Rankings</h1>
                <h2><a style="color: #B20000" href='/'>PiScout Database</a></h2>
                <br><br>
                <table class="tablesorter">
                <thead><tr>
                    <th>Rank</th>
                    <th>Team</th>
                    <th>RP</th>
                    <th>Match Score</th>
                    <th>Current RP</th>
                    <th>Current Match Score</th>
                </tr></thead>
                <tbody>
                {0}
                </tbody>
                </table>
            </body>
            </html>
        '''.format(output)

        
    
    def predictScore(self, teams, level='quals'):
        conn = sql.connect(self.datapath())
        cursor = conn.cursor()
        ballScore = []
        endGame = []
        autoGears = []
        teleopGears = []
        for n in teams:
            average = cursor.execute('SELECT * FROM averages WHERE team=?', (n,)).fetchall()
            assert len(average) < 2
            if len(average):
                entry = average[0]
            else:
                entry = [0]*8
            autoGears.append(entry[2])
            teleopGears.append(entry[3])
            ballScore.append((entry[5]+entry[6]))
            endGame.append((entry[7]))
        retVal = {'score': 0, 'gearRP': 0, 'fuelRP': 0}
        score = sum(ballScore[0:3]) + sum(endGame[0:3])
        if sum(autoGears[0:3]) >= 1:
            score += 60
        else:
            score += 40
        if sum(autoGears[0:3]) >= 3:
            score += 60
        elif sum(autoGears[0:3] + teleopGears[0:3]) >= 2:
            score += 40
        if sum(autoGears[0:3] + teleopGears[0:3]) >= 6:
            score += 40
        if sum(autoGears[0:3] + teleopGears[0:3]) >= 12:
            score += 40
            if level == 'playoffs':
                score += 100
            else:
                retVal['gearRP'] == 1
        if sum(ballScore[0:3]) >= 40:
            if level == 'playoffs':
                score += 20
            else:
                retVal['fuelRP'] == 1
        retVal['score'] = score
        return retVal
            
    #END OF CLASS

# Execution starts here
datapath = 'data_' + CURRENT_EVENT + '.db'

def keyFromItem(func):
    return lambda item: func(*item)
    
if not os.path.isfile(datapath):
    # Generate a new database with the three tables
    conn = sql.connect(datapath)
    cursor = conn.cursor()
    # Replace 36 with the number of entries in main.py
    cursor.execute('CREATE TABLE scout (key INTEGER PRIMARY KEY,' + ','.join([('d' + str(a) + ' integer') for a in range (22)]) + ',flag integer' + ')')
    cursor.execute('''CREATE TABLE averages (team integer,apr integer,autogear real,teleopgear real, geardrop real, autoballs real, teleopballs real, end real, defense real)''')
    cursor.execute('''CREATE TABLE maxes (team integer, apr integer, autogear real, teleopgear real, geardrop real, autoballs real, teleopballs real, end real, defense real)''')
    cursor.execute('''CREATE TABLE lastThree (team integer, apr integer, autogear real, teleopgear real, geardrop real, autoballs real, teleopballs real, end real, defense real)''')
    cursor.execute('''CREATE TABLE noDefense (team integer, apr integer, autogear real, teleopgear real, geardrop real, autoballs real, teleopballs real, end real, defense real)''')
    cursor.execute('''CREATE TABLE comments (team integer, comment text)''')
    conn.close()

conf = {
     '/': {
         'tools.sessions.on': True,
         'tools.staticdir.root': os.path.abspath(os.getcwd())
     },
     '/static': {
         'tools.staticdir.on': True,
         'tools.staticdir.dir': './public'
     },
    'global': {
        'server.socket_port': 8000
    }
}

#start method only to be used on the local version
#def start():
#    cherrypy.quickstart(ScoutServer(), '/', conf)

#the following is run on the real server
'''

conf = {
         '/': {
                 'tools.sessions.on': True,
                 'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/static': {
                 'tools.staticdir.on': True,
                 'tools.staticdir.dir': './public'
         },
        'global': {
                'server.socket_host': '0.0.0.0',
                'server.socket_port': 80
        }
}
'''
cherrypy.quickstart(ScoutServer(), '/', conf)

