<?php
include ("common.php");
$config = parse_ini_file(conf_file(), True);

if ($this->uri->segment(4, 0) === "getfile")
  {
    $pkgdir = $config["koji"]["pkgdir"];
    $rpmpath = $pkgdir . $pkg_info->build_name . "/" . $pkg_info->Version . "/" . $pkg_info->Rel . "/";
    $rpmpath .= $pkg_info->Arch . "/" . $pkg_info->nvr . "." . $pkg_info->Arch . ".rpm";

    ob_start();
    if ($pkg_info->Arch=='src')
      $command = "rpm2cpio " . $rpmpath . "| cpio -i --to-stdout " . substr($filepath,1);
    else
      $command = "rpm2cpio " . $rpmpath . "| cpio -i --to-stdout ." . $filepath;

    passthru($command);
    $stdout_result = ob_get_clean();

    $finfo = new finfo(FILEINFO_MIME);
    $ftype = $finfo->buffer($stdout_result);


    header('Content-Description: File Transfer');
    header('Content-Type: ' . $ftype);
    //header('Content-Disposition: attachment; filename='.basename($filepath));
    header('Content-Transfer-Encoding: binary');
    header('Expires: 0');
    header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
    header('Pragma: public');
    header('Content-Length: ' . $filesize);

    echo $stdout_result;
    return;

  }

ob_start('ob_tidyhandler');
$this->load->view("header");
?>
        <link href="<?=  base_url() ?>css/jquery-ui-1.8.4.custom.css" rel="stylesheet" type="text/css" />
        <script type="text/javascript" src="<?=  base_url() ?>js/jquery-ui-1.8.4.custom.min.js"></script>
  <script type="text/javascript">
  $(function(){
      
      // Tabs
      $('#tabs').tabs();
    });
  </script>

        <script type="text/javascript">
  function doMenu(item) {
  obj=document.getElementById(item);
  col=document.getElementById("x" + item);
  if (obj.style.display=="none") {
    obj.style.display="block";
    col.innerHTML="[-]";
  }
  else {
    obj.style.display="none";
    col.innerHTML="[+]";
  }
}
        </script>

<?
include("header.php");
echo GenMenu($user);
echo Bread($whereami);
include("searchform.php");
?>
		<div id="function_description">
<?php
  
  if ($pkg_info) 
    {
      $koji_addr = $config["koji"]["web_iface_public"];
      $koji_pkgdir = $config["koji"]["pkgdir_web"];
      if ($user)
	$koji_addr = $config["koji"]["web_iface_private"];
      $builddate= date('M d Y h:i A', $pkg_info->Date); 
      $rpmfilename = $pkg_info->nvr . "." . $pkg_info->Arch . ".rpm";
      $rpmurl = $koji_pkgdir . $pkg_info->build_name . "/" . $pkg_info->Version . "/" . $pkg_info->Rel . "/" . $pkg_info->Arch . "/" . $rpmfilename;
      $srpmfilename = $pkg_info->SRCRPM;
      $srpmurl = $koji_pkgdir . $pkg_info->build_name . "/" . $pkg_info->Version . "/" . $pkg_info->Rel . "/src/" . $srpmfilename;
      $output = "\n<div id='packageHeader'><h3>" . $pkg_info->Name . " " . $pkg_info->Version . "-" . $pkg_info->Rel . "<br/></h3>";
      $output .= "\n<table style='width: 100%; padding: 0; margin: 0; border: 0;'>\n<tr><td class='title' style='text-align: left; padding-left: 40px; padding-right: 40px;'>Summary</td></tr>";
      $output .= "\n<tr><td style='text-align: left; padding-left: 40px; padding-right: 40px;'>" . htmlentities($pkg_info->Summary, ENT_QUOTES) . "</td></tr>";

      $output .= "\n<tr><td class='title' style='text-align: left; padding-left: 40px; padding-right: 40px;'>Description</td></tr>";
      $output .= "\n<tr><td style='text-align: left; padding-left: 40px; padding-right: 40px;'>" . htmlentities($pkg_info->Description, ENT_QUOTES) . "</td></tr></table>";

      $output .= "</div>";
      $output .= "\n<table cellspacing='0' cellpadding='0' style='width: 100%;'><tr><td style='vertical-align: top; width: 33%; height: 100%' rowspan='2'>\n<table id='infoTable' style='height: 100%;'>";
      $output .= "\n<tr><td class='title'>Name</td><td>" . $pkg_info->Name . "</td></tr>";
      $output .= "\n<tr><td class='title'>Version</td><td>" . $pkg_info->Version . "</td></tr>";
      $output .= "\n<tr><td class='title'>Release</td><td>" . $pkg_info->Rel . "</td></tr>";
      $output .= "\n<tr><td class='title'>Platform</td><td>Linux/" . implode(", ", $arch_info). "</td></tr>";
      $output .= "\n<tr><td class='title'>Size</td><td>" . round($pkg_info->Size / 1024) ." KB</td></tr>";
	      
      if ($pkg_info->Category != NULL) $output .= "\n<tr><td class='title'>Category</td><td>" . $pkg_info->Category . "</td></tr>";
      $output .= "\n<tr><td class='title'>Vendor</td><td>". $pkg_info->Vendor . "</td></tr>";
      if ($pkg_info->URL != NULL and $pkg_info->URL != "[]") $output .= "\n<tr><td class='title'>URL</td><td><a href='" . $pkg_info->URL."'>" . $pkg_info->URL . "</a></td></tr>";
      $output .= "\n<tr><td class='title'>Distribution</td><td>\n<table id='resultsTable' style='margin-bottom: 0px;'>";
      foreach ($repos as $tag)
	{
	  $output .= "\n<tr><td class='" . $tag . "' style='border: 0px; padding: 3px 0px; text-align: left;'>" . $tag . "</td></tr>";
	}
      $output .=  "</table></td></tr>";
      $output .= "\n<tr><td class='title'>Built On</td><td>" . $builddate . "</td></tr>";
      $output .= "\n<tr><td class='title'>Built By</td><td>" . $pkg_info->BuiltBy . "</td></tr>";
      $output .= "\n<tr><td class='title'>License </td><td>" . $pkg_info->License . "</td></tr>";
      $output .= "\n<tr><td class='title'>Source RPM</td>\n<td><a href='" . $srpmurl . "'>" . $srpmfilename . "</a></td></tr>";
      
      foreach ($arch_info as $myarch)
	{
	  $rpmfilename = $pkg_info->nvr . "." . $myarch . ".rpm";
	  $rpmurl = $koji_pkgdir . $pkg_info->build_name . "/" . $pkg_info->Version . "/" . $pkg_info->Rel . "/" . $myarch . "/" . $rpmfilename;
	  $output .= "\n<tr><td class='title'>" . $myarch . "</td><td><a href='" . $rpmurl . "'>" . $rpmfilename . "</a></td></tr>";
	  if ($pkg_info->DBGRPM != "None")
	    {
	      $debugrpmfilename = $pkg_info->DBGRPM . "." . $myarch . ".rpm";
	      $debugrpmurl = $koji_pkgdir . $pkg_info->build_name . "/" . $pkg_info->Version . "/" . $pkg_info->Rel . "/" . $myarch . "/" . $debugrpmfilename;
	      $output .= "\n<tr><td class='title' style='text-align: left;'>Debug-" . $myarch . "</td><td><a href='" . $debugrpmurl . "'>" . $debugrpmfilename . "</a></td></tr>";
	    }
	}
      $build_id_link = $koji_addr . "buildinfo?buildID=" . $pkg_info->build_id;
      $package_id_link = $koji_addr . "packageinfo?packageID=" . $pkg_info->package_id;
      $output .= "\n<tr><td class='title'>Koji</td><td><a href='" . $build_id_link . "'>All RPMs from this build</a></td></tr>";
      $output .= "\n<tr><td class='title'></td><td><a href='" . $package_id_link . "'>All builds of this package</a></td></tr>";
      if ($user)
	$output .= "\n<tr><td class='title'>Publish</td><td><a href='" . site_url('index.php/queue/add/') . "/" . $pkg_info->build_id . "'>Add to Queue</a></td></tr>";


      $output .= "\n<tr style='height: 100%;'><!-- This is the filler row --><td></td></tr>";
      
      $output .= "\n</table></td><td style='width: 4px;'></td>\n<td style='vertical-align: top; height: 100%;'>";
      
      $output .= "\n\n<!-- Begin Tabs -->";

      $output .= "\n<div id='tabs' style='height: 100%;'>";
      $output .= "\n<ul style='-moz-border-radius: 0;'>";
      $output .= "\n<li><a href='#tabs-1'>Files</a></li>";
      $output .= "\n<li><a href='#tabs-2'>Sources</a></li>";
      $output .= "\n<li><a href='#tabs-3'>Dependencies</a></li>";
      $output .= "\n<li><a href='#tabs-4'>ChangeLogs</a></li>";
      $output .= "\n</ul>";


      //FILES
      $output .= "\n\n<!-- Begin Files -->";
      $output .= "\n<div id='tabs-1'>";
      if ($Files) 
	{
	  $rpmid = $this->uri->segment(3,0);
	  $output .= "\n<table class='resultsLine'>";
	  $output .= "\n<tr><td class='headeru' style='width: 80%; background: #ffffff;'>Name</td><td class='headeru' style='text-align: right; background: #ffffff;'>Size</td></tr>";
	  foreach ($Files as $files_info)
	    {
	      // Check if it is a directory
	      if ($files_info->Digest == "" and $files_info->Size == 4096)
		$output .= "\n<tr><td>" . $files_info->Path . "/</td><td style='text-align: right; padding-top: 2px; padding-bottom: 2px;'>directory</td></tr>";
	      else
		{
		$output .= "\n<tr><td style='padding-top: 2px; padding-bottom: 2px;'><a href='" .  "getfile" . $files_info->Path . "'>" . $files_info->Path . "</a></td>\n<td style='text-align: right;'><a href='"  . "getfile" . $files_info->Path . "'>" . $files_info->Size . "</a></td></tr>";
		}
	    }
	  $output .= "</table>";
	}
      else
	$output .= "\n<h3>No Files</h3>";

      $output .= "</div>";
      $output .= "\n<!-- End Files -->";

      //Source Files
      $output .= "\n\n<!-- Begin Sources -->";
      $output .= "\n<div id='tabs-2'>";
      if ($SRCFiles) 
	{
	  $output .= "\n<table class='resultsLine'>";
          $output .= "\n<tr><td class='headeru' style='width: 80%; background: #ffffff;'>Name</td><td class='headeru' style='text-align: right; background: #ffffff;'>Size</td></tr>";
	  $srpmid = $pkg_info->srpm_id;
	  foreach ($SRCFiles as $files_info)
	    $output .= "\n<tr><td style='padding-top: 2px; padding-bottom: 2px;'><a href='" . $srpmid . "/getfile/" . $files_info->Path . "'>" . $files_info->Path . "</a></td><td style='text-align: right;'><a href='" . $srpmid . "/getfile/" . $files_info->Path . "'>" . $files_info->Size . "</a></td></tr>";
	  $output .= "</table>";
	}
      else
	$output .= "\n<h3>No Sources</h3>";
      $output .= "</div>";
      $output .= "\n<!-- End Sources -->";

      //Dependencies:
      $output .= "\n\n<!-- Begin Dependencies -->";
      $output .= "\n<div id='tabs-3'>";
      $output .= "<table style='width: 100%;' cellspacing='0'>";

      $output .= "<tr><td style='width: 50%; vertical-align: top;'><table class='resultsLine'>";
      //Provides
      $output .= "\n\n<!-- Begin Provides -->";
      if ($Provides) 
	{
	  $output .= "\n<tr><td class='headeru' style='background: #ffffff;'>Provides</td></tr>";
	  foreach ($Provides as $provides_info) $output .= SortDep($provides_info , "provides");
	}
      else
	$output .= "\n<tr><td class='headeru' style='background: #ffffff;'>No Provides</td></tr>";
      $output .= "\n<!-- End Provides -->";

      $output .= "</table></td><td style='vertical-align: top;'><table class='resultsLine'>";
      //Requires
      $output .= "\n\n<!-- Begin Requires -->";
      if ($Requires) 
	{
	  $output .= "\n<tr><td class='headeru' style='background: #ffffff;'>Requires</td></tr>";
	  foreach ($Requires as $requires_info) $output .= SortDep($requires_info , "requires");
	}
      else
	$output .= "\n<tr><td class='headeru' style='background: #ffffff;'>No Requires</td></tr>";
      $output .= "\n<!-- End Requires -->";

      $output .= "</table></td></tr><tr><td style='vertical-align: top;'><table class='resultsLine'>";
      //Obsoletes
      $output .= "\n\n<!-- Begin Obsoletes -->";
      if ($Obsoletes) 
	{
	  $output .= "\n<tr><td class='headeru' style='background: #ffffff;'>Obsoletes</td></tr>";
	  foreach ($Obsoletes as $obsoletes_info) $output .= SortDep($obsoletes_info , "obsoletes");
	}
      else
	$output .= "\n<tr><td class='headeru' style='background: #ffffff;'>No Obsoletes</td></tr>";
      $output .= "\n<!-- End Obsoletes -->";
      
      $output .= "</table></td><td style='vertical-align: top;'><table class='resultsLine'>";
      //Conflicts
      $output .= "\n\n<!-- Begin Conflicts -->";
      if ($Conflicts) 
	{
	  $output .= "\n<tr><td class='headeru' style='background: #ffffff;'>Conflicts</td></tr>";
	  foreach ($Conflicts as $conflicts_info) $output .= SortDep($conflicts_info , "conflicts");
	}
      else
	$output .= "\n<tr><td class='headeru' style='background: #ffffff;'>No Conflicts</td></tr>";
      $output .= "\n<!-- End Conflicts -->";

      $output .= "</table></td></tr>";

      $output .= "</table>";
      $output .= "</div>";// end Dependencies
      $output .= "\n<!-- End Dependencies -->";

      //ChangeLogs
      $output .= "\n\n<!-- Begin ChangeLogs -->";
      $output .= "\n<div id='tabs-4'>";
      //Spec ChangeLog
      $output .= "\n\n<!-- Begin Spec ChangeLog -->";
      $output .= "\n<table class='clogTable' style='vertical-align: top; height: 100%;' cellspacing='0'>";

      $clog2display = 3;
      if (sizeof($clog_info) > $clog2display)
	$output .= "\n<tr><td class='headeru'>Specfile ChangeLog<a href=\"JavaScript:doMenu('clog');\" id='xclog'>[+]</a></td></tr>";
      else
	$output .= "\n<tr><td class='headeru'>Specfile ChangeLog</td></tr>";
      $output .= "\n<tr><td>";

      for ($i=0; $i < min($clog2display,sizeof($clog_info)); ++$i)
	{
	  $cl_date = date('D M d Y', $clog_info[$i]->Date);
	  $cl_author = htmlentities(CfcAuthor($clog_info[$i]->Author), ENT_QUOTES);
	  $cl_text = htmlentities($clog_info[$i]->Text, ENT_QUOTES);
	  $cl_text = str_replace("\n", "<br/>\n", $cl_text);
	  $cl_text = preg_replace("@(http|https|ftp)(://)(\S+)@","<a href='$1$2$3' onclick='return ! window.open(this.href);'>$1$2$3</a>", $cl_text);
	  $output .= "\n* " . $cl_date . " " . $cl_author . "<br/>";
	  $output .= "\n" . $cl_text . "<br/>"; 
	}
      if (sizeof($clog_info) > $clog2display)
	{
	  $output .= "\n<div style='display: none' id='clog'>";
	  for ($i=5; $i < sizeof($clog_info); ++$i)
	    {
	      $cl_date = date('D M d Y', $clog_info[$i]->Date);
	      $cl_author = htmlentities(CfcAuthor($clog_info[$i]->Author), ENT_QUOTES);
	      $cl_text = htmlentities($clog_info[$i]->Text, ENT_QUOTES);
	      $cl_text = str_replace("\n", "<br/>\n", $cl_text);
	      $cl_text = preg_replace("@(http|https|ftp)(://)(\S+)@","<a href='$1$2$3' onclick='return ! window.open(this.href);'>$1$2$3</a>", $cl_text);
	      $output .= "\n* " . $cl_date . " " . $cl_author . "<br/>";
	      $output .= "\n" . $cl_text . "<br/>";
	    }
	  $output .= "\n</div>";
	}
      $output .= "\n</td></tr></table>";
      $output .= "\n<!-- End Spec ChangeLog -->";

      //Software ChangeLog
      if ($swclog_info)
	{
	  $output .= "\n\n<!-- Begin Software Changelog -->";
	  $output .= "\n<table class='clogTable' style='vertical-align: top; height: 100%;' cellspacing='0'>";
	  $swcloglines2display = 8;
	  $output .= "\n<tr><td class='headeru ttip' id='swclogtip'>Software ChangeLog";

	  if (sizeof($swclog_info->Text) > $swcloglines2display)
	    $output .= "\n<a href=\"JavaScript:doMenu('swclog');\" id='xswclog'>[+]</a>";
	  $output .= "</td></tr>";
	  $output .= "\n<tr><td>";
	  
	  for ($i=0; $i < min($swcloglines2display,sizeof($swclog_info->Text)); ++$i)
	    {
	      $swcl_line = htmlentities($swclog_info->Text[$i], ENT_QUOTES);
	      $swcl_line = str_replace("\t", "&nbsp;&nbsp;", $swcl_line);
	      $swcl_line = preg_replace("@(http|https|ftp)(://)(\S+)@","<a href='$1$2$3' onclick='return ! window.open(this.href);'>$1$2$3</a>", $swcl_line);
	      $output .= "\n" . $swcl_line . "<br/>"; 
	    }
	  if (sizeof($swclog_info->Text) > $swcloglines2display)
	    {
	      $output .= "\n<div style='display: none' id='swclog'>";
	      for ($i=$swcloglines2display; $i < sizeof($swclog_info->Text); ++$i)
		{
		  $swcl_line = htmlentities($swclog_info->Text[$i], ENT_QUOTES);
		  $swcl_line = preg_replace("@(http|https|ftp)(://)(\S+)@","<a href='$1$2$3' onclick='return ! window.open(this.href);'>$1$2$3</a>", $swcl_line);
		  $output .= "\n" . $swcl_line . "<br/>";
		}
	      $output .= "\n</div>";
	    }
	  $output .= "\n</td></tr>";
	  $output .= "</table>";
	  $output .= "\n<!-- End Software ChangeLog -->";
	}
      $output .= "</div>";// end ChangeLogs
      $output .= "\n<!-- End ChangeLogs -->";

      $output .= "</div>";// end tabs
      $output .= "\n<!-- End Tabs -->";

      $output .= "\n</td></tr>";
      $output .= "\n</table>";
      if ($swclog_info)
	$output .= "\n<div id='tswclogtip' class='queuetips'>From file: " . $swclog_info->Filename . "</div>";

      print $output;
    } 
  else 
    {
      echo "<p>Sorry, no results returned.</p>";
    }
	
?>
</div>
<?php
$this->load->view("footer");
?>
