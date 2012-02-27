# MySQL-Front 3.2  (Build 13.6)

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES */;

/*!40101 SET NAMES latin1 */;
DROP TABLE IF EXISTS `functions`;
CREATE TABLE `functions` (
  `function_id` int(11) NOT NULL auto_increment,
  `function_name` varchar(25) default '',
  `function_description` varchar(255) default NULL,
  PRIMARY KEY  (`function_id`)
) TYPE=MyISAM;

INSERT INTO `functions` VALUES (1,'random_element()','Takes an array as input and returns a random element from it.');
INSERT INTO `functions` VALUES (2,'set_cookie()','Sets a cookie containing the values you specify.');
INSERT INTO `functions` VALUES (3,'mdate()','This function is identical to PHPs date() function, except that it lets you use MySQL style date codes, where each code letter is preceded with a percent sign: %Y %m %d etc.');
INSERT INTO `functions` VALUES (4,'local_to_gmt()','Takes a Unix timestamp as input and returns it as GMT.');
INSERT INTO `functions` VALUES (5,'gmt_to_local()','Takes a Unix timestamp (referenced to GMT) as input, and converts it to a localized timestamp based on the timezone and Daylight Saving time submitted.');
INSERT INTO `functions` VALUES (6,'mysql_to_unix()','Takes a MySQL Timestamp as input and returns it as Unix.');
INSERT INTO `functions` VALUES (7,'unix_to_human()','Takes a Unix timestamp as input and returns it in a human readable format');
INSERT INTO `functions` VALUES (8,'human_to_unix()','Takes a \"human\" time as input and returns it as Unix.');
INSERT INTO `functions` VALUES (9,'timespan()','Formats a unix timestamp so that is appears similar to this: 1 Year, 10 Months, 2 Weeks, 5 Days, 10 Hours, 16 Minutes');
INSERT INTO `functions` VALUES (10,'days_in_month()','Returns the number of days in a given month/year. Takes leap years into account.');
INSERT INTO `functions` VALUES (11,'timezone_menu()','Generates a pull-down menu of timezones');
INSERT INTO `functions` VALUES (12,'directory_map(\'source dir','This function reads the directory path specified in the first parameter and builds an array representation of it and all its contained files.');
INSERT INTO `functions` VALUES (13,'read_file(\'path\')','Returns the data contained in the file specified in the path.');
INSERT INTO `functions` VALUES (14,'write_file(\'path\', $data)','Writes data to the file specified in the path. If the file does not exist the function will create it.');
INSERT INTO `functions` VALUES (15,'delete_files(\'path\')','Deletes ALL files contained in the supplied path.');
INSERT INTO `functions` VALUES (16,'heading()','Lets you create HTML &lt;h1&gt; tags. The first parameter will contain the data, the second the size of the heading.');
INSERT INTO `functions` VALUES (17,'nbs()','Generates non-breaking spaces (&amp;nbsp;) based on the number you submit.');
INSERT INTO `functions` VALUES (18,'br()','Generates line break tags (&lt;br /&gt;) based on the number you submit.');
INSERT INTO `functions` VALUES (19,'word_limiter()','Truncates a string to the number of words specified.');
INSERT INTO `functions` VALUES (20,'character_limiter()','Truncates a string to the number of characters specified. It maintains the integrity of words so the character count may be slightly more or less then what you specify.');
INSERT INTO `functions` VALUES (21,'ascii_to_entities()','Converts ASCII values to character entities, including high ASCII and MS Word characters that can cause problems when used in a web page, so that they can be shown consistently regardless of browser settings or stored reliably in a database.');
INSERT INTO `functions` VALUES (22,'entities_to_ascii()','This function does the opposite of the previous one; it turns character entities back into ASCII.');
INSERT INTO `functions` VALUES (23,'word_censor()','Enables you to censor words within a text string. The first parameter will contain the original string. The second will contain an array of words which you disallow. The third (optional) parameter can contain a replacement value for the words.');
INSERT INTO `functions` VALUES (24,'highlight_code()','Colorizes a string of code (PHP, HTML, etc.).');
INSERT INTO `functions` VALUES (25,'highlight_phrase()','Will highlight a phrase within a text string. The first parameter will contain the original string, the second will contain the phrase you wish to highlight.');
INSERT INTO `functions` VALUES (26,'word_wrap()','Wraps text at the specified character count while maintaining complete words.');
INSERT INTO `functions` VALUES (27,'auto_typography()','Formats text so that it is semantically and typographically correct HTML.');
INSERT INTO `functions` VALUES (28,'nl2br_except_pre()','Converts newlines to &lt;br /&gt; tags unless they appear within &lt;pre&gt; tags. This function is identical to the native PHP nl2br() function, except that it ignores &lt;pre&gt; tags.');
INSERT INTO `functions` VALUES (29,'site_url()','Returns your site URL, as specified in your config file. The index.php file (or whatever you have set as your site index_page in your config file) will be added to the URL, as will any URI segments you pass to the function.');
INSERT INTO `functions` VALUES (30,'base_url()','Returns your site base URL, as specified in your config file.');
INSERT INTO `functions` VALUES (31,'index_page()','Returns your site \"index\" page, as specified in your config file.');
INSERT INTO `functions` VALUES (32,'anchor()','Creates a standard HTML anchor link based on your local site URL');
INSERT INTO `functions` VALUES (33,'mailto()','Creates a standard HTML email link.');
INSERT INTO `functions` VALUES (34,'safe_mailto()','Identical to the above function except it writes an obfuscated version of the mailto tag using ordinal numbers written with JavaScript to help prevent the email address from being harvested by spam bots.');
INSERT INTO `functions` VALUES (35,'auto_link()','Automatically turns URLs and email addresses contained in a string into links.');
INSERT INTO `functions` VALUES (36,'url_title()','Takes a string as input and creates a human-friendly URL string. This is useful if, for example, you have a blog in which you\'d like to use the title of your entries in the URL.');
INSERT INTO `functions` VALUES (37,'prep_url()','This function will add http:// in the event it is missing from a URL.');
INSERT INTO `functions` VALUES (38,'redirect()','Does a \"header redirect\" to the local URI specified. Just like other functions in this helper, this one is designed to redirect to a local URL within your site.');
INSERT INTO `functions` VALUES (39,'xml_convert(\'string\')','Takes a string as input and converts the reserved XML characters to entities');

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
