<?php  if (!defined('BASEPATH')) exit('No direct script access allowed');
/*
| -------------------------------------------------------------------
| DATABASE CONNECTIVITY SETTINGS
| -------------------------------------------------------------------
| This file will contain the settings needed to access your database.
|
| For complete instructions please consult the "Database Connection"
| page of the User Guide.
|
| -------------------------------------------------------------------
| EXPLANATION OF VARIABLES
| -------------------------------------------------------------------
|
|	['hostname'] The hostname of your database server.
|	['username'] The username used to connect to the database 
|	['password'] The password used to connect to the database 
|	['database'] The name of the database you want to connect to
|	['dbdriver'] The database type. ie: mysql.  Currently supported:
				 mysql, mysqli, postgre, odbc, mssql
|	['dbprefix'] You can add an optional prefix, which will be added 
|				 to the table name when using the  Active Record class
|	['pconnect'] TRUE/FALSE - Whether to use a persistent connection
|	['db_debug'] TRUE/FALSE - Whether database errors should be displayed.
|	['active_r'] TRUE/FALSE - Whether to load the active record class
|
| The $active_group variable lets you choose which connection group to
| make active.  By default there is only one group (the "default" group).
|
*/

$active_group = "centos6";

$db['centos6']['hostname'] = "192.168.226.90";
$db['centos6']['username'] = "roji";
$db['centos6']['password'] = "yellow";
$db['centos6']['database'] = "rpmfind_centos6";
$db['centos6']['dbdriver'] = "mysql";
$db['centos6']['dbprefix'] = "";
$db['centos6']['active_r'] = TRUE;
$db['centos6']['pconnect'] = FALSE;
$db['centos6']['db_debug'] = TRUE;

?>
