<?php  if (!defined('BASEPATH')) exit('No direct script access allowed');

/* The config file of rutgers-repotools */
function conf_file()
{
  $obj =& get_instance();
  return $obj->config->item('conf_file');
}

/* Title to display on the title bar of the browser */
function get_title()
{
  $obj =& get_instance();
  return $obj->config->item('site_title');
}

/* Help link from the tiki */
function get_help()
{
  $obj =& get_instance();
  return $obj->config->item('help_page');
}

/* Main server where the rpm2php is linked to */
function get_mother_host()
{
  $obj =& get_instance();
  return $obj->config->item('mother_host');
}

/* Greeting message to display in the header */
function get_greeting_msg()
{
  $obj =& get_instance();
  return $obj->config->item('greeting_msg');
}

/* Public version of rpm2php or private */
function is_rpm2php_priv()
{
  $obj =& get_instance();
  return $obj->config->item('private');
}

?>
