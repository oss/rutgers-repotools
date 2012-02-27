<?php
ob_start('ob_tidyhandler');
include("common.php");
$this->load->view("header");
include("header.php");
echo GenMenu($user);
echo Bread($whereami);
include("searchform.php");
?>
  <div id="function_description">
  <?= SortSearchResults($search_results, $user, "No recent packages published."); ?>
  </div>

<?php
$this->load->view("footer");
?>