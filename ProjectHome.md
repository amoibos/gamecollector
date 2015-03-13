Command line tool for managing your collection with the power of python and sqlite. You can import and export your database with less than 1KLOC.

<img src='http://gamecollector.googlecode.com/hg/screenshot.png' height='400' width='600'>

The gamecollector uses sqlite for storing the data and gzip for compression. When you start the collector without database path, gamecollector try to import the data from the home directory database 'collect_dump.gz'. After exit the in-memory database will be written back. An info parameter give you the current version in the command line. Almost all dialogs can abort with "!". You can use python 2 or 3 and also switching between these versions is supported.<br>
<br>
All commands within the program have a long and a short identifier. The following <b>commands</b> are available:<br>
<table><thead><th>long name </th><th> shortened </th><th> description </th></thead><tbody>
<tr><td>exit </td><td> x </td><td> terminate and commit all changes to the database</td></tr>
<tr><td>list </td><td> l (/p) (sorting column) </td><td> list all records, optional block view and sorting(default title) </td></tr>
<tr><td>switch </td><td> + </td><td> invert current mode(read only and writable)</td></tr>
<tr><td>longnames </td><td> <code>*</code> </td><td> invert presentation mode for full size columns</td></tr>
<tr><td>eval TERM</td><td> = TERM </td><td> compute term </td></tr>
<tr><td>help </td><td> ? </td><td> print all commands</td></tr>
<tr><td>add </td><td> a </td><td> asks all necessary infos and add this record </td></tr>
<tr><td>delete WHERE CLAUSE </td><td> d WHERE CLAUSE </td><td> delete record(s)</td></tr>
<tr><td>update </td><td> u WHERE CLAUSE </td><td> update record(s)</td></tr>
<tr><td>search </td><td> s WHERE CLAUSE </td><td> search for records</td></tr>
<tr><td>import </td><td> i </td><td> import from a csv formated file </td></tr>
<tr><td>export </td><td> e </td><td> export from a csv formated file </td></tr>
<tr><td>raw </td><td> r </td><td> sql query bypass </td></tr></tbody></table>

The following <b>columns</b> are defined in the table:<br>
<table><thead><th>column identifier </th><th> data type </th><th> description </th></thead><tbody>
<tr><td>title </td><td>string</td><td> unique identifier that is never empty</td></tr>
<tr><td>box </td><td> string </td><td> only false or true are available</td></tr>
<tr><td>manual </td><td> string  </td><td> only false or true are available</td></tr>
<tr><td>cartridge </td><td> string </td><td> only false or true are available</td></tr>
<tr><td>region </td><td> string </td><td> something like PAL, JAP, BRA</td></tr>
<tr><td>price</td><td> integer </td><td> a number withour currency</td></tr>
<tr><td>condition </td><td>integer </td><td> a number lower is better</td></tr>
<tr><td>date </td><td>  integer </td><td> last two digits of the year and 2 digits for the month</td></tr>
<tr><td>special </td><td> string </td><td> name for special version </td></tr>
<tr><td>comment</td><td> string</td><td> comments or other stuff</td></tr></tbody></table>

You can use the like operator for inact search like 'search like "%ario%"'. Some columns need quotes(string) and others not. In the command mode you can use the history of your shell. All changes in the database were saved after termination of the application.