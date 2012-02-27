<?php

function Bread($whereami)
{
  $bread = "<div id='breadcrumbs'>";
  $mother = get_mother_host();
  $mother_short = str_replace("http://", "", $mother);
  $mother_short = str_replace("https://", "", $mother_short);

  $bread .= "<a href='" . $mother . "'>" . $mother_short . "</a> &gt; ";
  $bread .= "<a href='" . site_url() . "'>" . get_title() . "</a> &gt; ";
  foreach ($whereami as $pos)
    $bread .= $pos . " &gt; ";
  $bread = substr($bread, 0, -6) . "</div>";
  return $bread;
}

function GenMenu($user, $queuelist=FALSE)
{
  $config = parse_ini_file(conf_file(), True);
  $mymenu = "<div id='menu'>";
  $mymenu .= "\n  <div style = 'float: left; padding-left: 10px; padding-top: 5px;'>";
  if ($user)
    $mymenu .= "Hello " . $user . ". ";
  $mymenu .= get_greeting_msg(). "</div>";

  if (is_rpm2php_priv())
    {
      $mymenu .= "<div style='float: right; padding-right: 10px; padding-top: 5px;'>";
      
      if ($user)
	{
	  $mymenu .= "<a href='" . get_help() . "' onclick='return ! window.open(this.href);'>Help</a> - ";
	  $urlarray = explode("://", site_url("logout.php"));
	  $url = $urlarray[0] . "://log:out@" . $urlarray[1];
	  $mymenu .= checkQueue($queuelist);
	  $mymenu .= " - <a href='" . $config["koji"]["web_iface_private"] . "' onclick='return ! window.open(this.href);'>Koji</a>";
	  $mymenu .= " - <a href='" . $url . "'>Logout</a>";
	}
      else
	$mymenu .= "<a href='" . site_url("login.php") . "'>Login</a>";
      $mymenu .= "\n  </div>";
    }
  else
    {
      // FIXME: Apache for public network runs on a different machine than omachi
      //        so this script can't access /var/lock/ of omachi
      //        How should we handle this?
      $mymenu .= "<div style='float: right; padding-right: 10px; padding-top: 5px;'>";
      $chk = checkQueue($queuelist, True);
      if ($chk)
	$mymenu .= $chk . " - ";
      $mymenu .= "<a href='" . $config["koji"]["web_iface_public"] . "' onclick='return ! window.open(this.href);'>Koji</a>";
      $mymenu .= "\n</div>";
    }

  $mymenu .= "\n</div>";
  return $mymenu;
}
function endsWith($haystack, $needle)
{
    $length = strlen($needle);
    $start  = $length * -1; //negative
    return (substr($haystack, $start) === $needle);
}


function SortSearchResults($search_results, $user, $fail_message="Sorry, no results returned.")
{
  $config = parse_ini_file(conf_file(), True);
  $allrepos = explode(" ", $config["repositories"]["allrepos"]);
  $allrepos_display = explode(" ", $config["repositories"]["allrepos_display"]);
  $distname = $config["repositories"]["distname"];
  $distver = $config["repositories"]["distver"];
  $dontpublishrepos = explode(" ", $config["repositories"]["dontpublishrepos"]);
  $dontpublishrepos_display = explode(" ", $config["repositories"]["dontpublishrepos_display"]);
  $publishrepos = $allrepos;
  foreach ($dontpublishrepos as $drepo)
    {
      $dkey = array_search($drepo, $publishrepos);
      if ($dkey !== False)
	unset($publishrepos[$dkey]);
    }
  $publishrepos_display = $allrepos_display;
  foreach ($dontpublishrepos_display as $drepo)
    {
      $dkey = array_search($drepo, $publishrepos_display);
      if ($dkey !== False)
	unset($publishrepos_display[$dkey]);
    }
  for ($i=0; $i < sizeof($allrepos); ++$i)
    #$allrepos[$i] = $distname . $distver . "-" . $allrepos[$i];

  $distname = $config["repositories"]["distname"];
  $distver = $config["repositories"]["distver"];
  for ($i=0; $i < sizeof($publishrepos); ++$i)
    #$publishrepos[$i] = $distname . $distver . "-" . $publishrepos[$i];
  
  $output = "";
  $output .= "<script type='text/javascript' src='" . base_url() ."js/js_tooltips.js'></script>";
  $output .= "\n<table id='resultsTable'>";
  $output .="\n<tr><th>Name</th>\n<th>Summary</th>";
  if ($user)
    foreach ($allrepos_display as $reponame)
      $output .= "\n<th style='width: 90px;'>" . $reponame . "</th>";
  else
    foreach ($publishrepos_display as $reponame)
      $output .= "\n<th style='width: 90px;'>" . $reponame . "</th>";
  
  $output .= "\n<th style='width: 76px;'>Arch</th></tr>";

  if($search_results)
    {
      $pkgarray = array();
      $display_results = array();
      foreach ($search_results as $function_info) 
	{
	  $mypos = array_search($function_info->Name, $pkgarray);
	  if ($mypos === FALSE)
	    {
	      $pkgarray[] = $function_info->Name;
	      $pkg = new StdClass;
	      $pkg->Name = $function_info->Name;
	      $pkg->Summary = $function_info->Summary;
	      $repo = $function_info->repo;
	      $pkg->$repo = new StdClass;
	      $pkg->$repo->vr = $function_info->Version . "-" . $function_info->Rel;
	      $pkg->$repo->rpm_id = $function_info->rpm_id;
	      $pkg->$repo->build_id = $function_info->build_id;
	      $pkg->Archs = array($function_info->Arch);
	      $pkg->$repo->Centos_Version = $function_info->Centos_Version;
	      $display_results[] = $pkg;
	    }
	  else
	    {
	      for ($i=0; $i < sizeof($display_results); ++$i)
		{
		  if ($display_results[$i]->Name == $function_info->Name)
		    {
		      $repo = $function_info->repo;
		      if (isset($display_results[$i]->$repo))
			{
			  if ($display_results[$i]->$repo->build_id > $function_info->build_id)
			    {
			      continue;
			    }
			}
		      else
			$display_results[$i]->$repo = new StdClass;
		      $display_results[$i]->$repo->vr = $function_info->Version . "-" . $function_info->Rel;
		      
		      if (isset($display_results[$i]->$repo->rpm_id))
			  {
			    if ($function_info->Arch == $config["repositories"]["arch_display"])
			      $display_results[$i]->$repo->rpm_id = $function_info->rpm_id;
			  }
			  else
			$display_results[$i]->$repo->rpm_id = $function_info->rpm_id;
		      $display_results[$i]->$repo->build_id = $function_info->build_id;
		      $display_results[$i]->$repo->Centos_Version= $function_info->Centos_Version;
		      if (in_array($function_info->Arch, $display_results[$i]->Archs) == FALSE)
			{
			  $display_results[$i]->Archs[] = $function_info->Arch;
			  sort($display_results[$i]->Archs);
			}
		    }
		}
	    }
	}
      $divinfo = "";
	  print "</pre>";
	
      foreach ($display_results as $display_info)
	{
	  if(strlen($display_info->Name)  > 30)
	    {
	      $display_info->Name=substr($display_info->Name,0,23) . "..." . substr($display_info->Name,-4); 
	    }
	  $output .= "\n<tr><td><strong>" . $display_info->Name . '</strong></td>';
	  $output .= "\n<td>" . htmlentities($display_info->Summary) . '</td>';

	  if ($user)
	    $reposarray = $allrepos;
	  else
	    $reposarray = $publishrepos;
	  foreach ($reposarray as $myrepo){
		  $output .= "<td class='$myrepo'>";
		
		  foreach($display_info as $field => $val){
		  
		  if (endsWith($field,$myrepo))
		  {
			  #print_r($val);
			  #$fixurl = site_url('index.php/packages/index/'.$display_info->$myrepo->rpm_id.'');
			  $fixurl = site_url('index.php/packages/index/'.$display_info->$field->rpm_id.'/' . $display_info->$field->Centos_Version );
			  $output .= "<strong><a href='" . $fixurl . "'>" . $display_info->$field->vr . " (" . $display_info->$field->Centos_Version . ")</a></strong></br>";
			  #$cvr = CuteVR($myrepo, $fixurl, $display_info->$myrepo->vr, $display_info->$myrepo->rpm_id);
			 # $cvr = CuteVR($myrepo, $fixurl, $display_info->$field->vr, $display_info->$field->rpm_id);
			#  $output .= $cvr[0];
			 # $divinfo .= $cvr[1];
		  }
		  else
		  {
		#	  $output .= "\n<td class='" . $myrepo . "'></td>";
		  }
	  }
	$output .= "</td>";
	}
	  $output .= "\n<td>" . implode(", ", $display_info->Archs) . '</td></tr>';
	}
      $output .= "\n</table>";
      $output .= $divinfo;
      
    } else{
    $output = "\n<p>" . $fail_message . "</p>";
  }
  return $output;
}

function CuteVR($repo, $url, $vr, $rpm_id)
{
  $cutat = 12;
  if(strlen($vr)  > $cutat+3)
    {
      $vrcut=substr($vr,0,$cutat) . "...";
      $output = "\n<td class='" . $repo . "'><strong><a href='" . $url . "'><span class='ttip' id='" . $repo . "-" . $rpm_id . "'>" . $vrcut . "</span></a></strong></td>";
      $divinfo ="\n<div id='t" . $repo . "-" . $rpm_id . "' class='info-" . $repo . "'>" . $vr . "</div>";
    }
  else
    {
      $output = "\n<td class='" . $repo . "'><strong><a href='" . $url . "'>" . $vr . "</a></strong></td>";
      $divinfo = NULL;
    }
  return array($output, $divinfo);
}

function getCookie()
{
  $queuelist = explode("s", $_COOKIE['QueuedRPMs']);

  for ($i=0; $i<sizeof($queuelist); ++$i)
    if (is_numeric($queuelist[$i]) == FALSE)
      unset($queuelist[$i]);

  return $queuelist;
}

function isPushInProgress()
{
 if (file_exists("/var/lock/rutgers-repotools/pushpackage"))
   return TRUE;
 else
   return FALSE;
}

function isUpdateDbInProgress()
{
 if (file_exists("/var/lock/rutgers-repotools/populate-rpmfind-db"))
   return TRUE;
 else
   return FALSE;
}

function checkQueue($queuelist=False, $lite=False)
{
  $mystring = "";
  if ($lite)
    {
      if (isPushInProgress())
	$mystring .= " Push in progress ";
      if (isUpdateDbInProgress())
	$mystring .= " Database update in progress ";
    }
  else
    {
      if (isPushInProgress())
	$mystring .= "<a href='" . site_url("index.php/push/index/") . "'> Push in progress</a>";
      else
	{
	  if ($queuelist === False and isset($_COOKIE['QueuedRPMs']))
	    $queuelist = getCookie();
	  
	  $queuesize = sizeof($queuelist);
	  if ($queuesize == 1 and is_array($queuelist))
	    $mystring .= " <a href='" . site_url("index.php/queue/index/") . "'> 1 package in queue</a>";
	  elseif ($queuesize > 1 and is_array($queuelist))
	    $mystring .= "<a href='" . site_url("index.php/queue/index/") . "'>" . $queuesize . " packages in queue</a>";
	  else
	    $mystring .= " No packages in queue";
	}

      $mystring .= " - ";
      
      if (isUpdateDbInProgress())
	$mystring .= "<a href='" . site_url("index.php/updatedb/index/") . "'>Database update in progress</a>";
      else
	$mystring .= "<a href='" . site_url("index.php/updatedb/index/") . "'>Update database</a>";
    }
  return $mystring;
}

function CfcAuthor($string)
{
  $ltpos = strpos($string, '<');
  $gtpos = strpos($string, '>');

  if ($ltpos === False or $gtpos === False)
    return htmlentities($string, ENT_QUOTES);

  $email = substr($string,$ltpos-1,$gtpos-$ltpos+2);
  $email = str_replace(array('@', '.'), array(' [at] ', ' [dot] '), $email);
  $final = substr($string,0, $ltpos) . $email . substr($string,$gtpos+1);
  return $final;
  }

function SortDep($dep_obj, $dep_type = NULL)
{
  //dependency flags
  $RPMSENSE_LESS = 2;
  $RPMSENSE_GREATER = 4;
  $RPMSENSE_EQUAL = 8;
  $output = "";

  $mydep = $dep_obj->Resource;
  if ($dep_obj->Flags)
    {
      if ($dep_obj->Flags & ($RPMSENSE_LESS | $RPMSENSE_GREATER | $RPMSENSE_EQUAL))
        {
          $mydep .= " ";
          if ($dep_obj->Flags & $RPMSENSE_LESS) $mydep .= "&lt;";
          if ($dep_obj->Flags & $RPMSENSE_GREATER) $mydep .= "&gt;";
          if ($dep_obj->Flags & $RPMSENSE_EQUAL) $mydep .= "= ";
          if ($dep_obj->Version) $mydep .= $dep_obj->Version;
        }
    }
  $output .= "\n<tr><td style='padding-top: 2px; padding-bottom: 2px;'>";
  if ($dep_type)
    $output .= "\n<a href='" . site_url('index.php/' . $dep_type . '/index/' . $dep_obj->Resource) . "'>" . $mydep . "</a>";
  else
    $output .= "\n" . $mydep;
  $output .= "\n</td></tr>";
  return $output;
}



?>
