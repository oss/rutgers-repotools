<?php
require_once(BASEPATH."libraries/Controller.php");

class Search_model extends Model
{
    function Search_model()
    {
        parent::Model();
        $obj =& get_instance();
        $this->config = parse_ini_file($obj->config->item('conf_file'), True);
        $this->config_for_6 = parse_ini_file($obj->config->item('conf_file6'), True);
        $this->db_centos6 = $obj->_ci_init_database($params = 'centos6', $return = TRUE, $active_record = FALSE, $centos_version='-centos6');
    }


    function ajaxSearch ($centos_version="both", $return_mode="string")
    {
        $sql = "select DISTINCT Name from Packages";

        //if we want results from both versions of centos, run them both recursively, and return the combined results
        if(strcmp($centos_version, "both") ==0){
            $result_5 = $this->ajaxSearch($centos_version='5', $return_mode='array');
            $result_6 = $this->ajaxSearch($centos_version='6', $return_mode='array');
            $toReturn = array_merge($result_5,$result_6);
            $toReturn = array_unique($toReturn);
            if ($toReturn === " " || $toReturn === array()){
                return '<p>Sorry, no results returned.</p>';
            }else{
                // convert array to string so we can return it
                $output = "";
                foreach($toReturn as $name){
                    $output .= '"' . $name . '",';
                }
                return $output;
            }

        }elseif( strcmp($centos_version , "6") == 0){
            $query = $this->db_centos6->query($sql); 
        }else{
            $query = $this->db->query($sql); 
        }

        if ($query->num_rows() > 0) 
        {
            $output = "";
            foreach ($query->result() as $function_info) 
            {
                if($return_mode === "string"){
                    $output .= '"' . $function_info->Name . '",';
                }else{
                    $output[] = $function_info->Name;
                }
            }
            return $output ;
        } 
        else 
        {
            if($return_mode === "string"){
                return '<p>Sorry, no results returned.</p>';
            }else{
                return array();
            }
        }
    }


    function SearchPackages ($searchTerm, $searchType, $user=False, $centos_version='both')
    {
        $hide_clause = "";
        if ($user == FALSE)
        {
            $dontpublishrepos = $this->config["repositories"]["dontpublishrepos"];
            $hide_clause = "and NOT repo='" . $dontpublishrepos . "'";
        }
        $sql = "";
        switch ($searchType) 
        {
            case "name":
                $sql = "select p.Name as Name, p.Version as Version , p.Rel as Rel, p.nvr as nvr, p.Summary as Summary, r.repo as repo, p.Arch as Arch, p.rpm_id as rpm_id, p.build_id as build_id from Packages as p inner join Distribution as r on r.rpm_id=p.rpm_id where p.Arch!='src' and p.Name like '%" . $this->db->escape_str($searchTerm) . "%' " . $hide_clause . " order by p.Name asc, repo, p.Version desc, p.Rel desc";
            break;
            case "file":
                $sql = "SELECT DISTINCT p.Name as Name, p.rpm_id as rpm_id, p.build_id as build_id, p.Version as Version , p.Rel as Rel, p.nvr as nvr, p.Summary as Summary, r.repo as repo, p.Arch as Arch FROM Files  LEFT JOIN Packages AS p ON (Files.rpm_id=p.rpm_id) LEFT JOIN Distribution AS r ON (p.rpm_id=r.rpm_id) where p.Arch!='src' and Files.Path LIKE '%" . $this->db->escape_str($searchTerm) . "%' " . $hide_clause . " order by p.Name asc, repo, p.Version desc, p.Rel desc";
            break;
            case "letter":
                $sql = "SELECT DISTINCT p.Name as Name, p.build_id as build_id, p.rpm_id as rpm_id, p.Version as Version , p.Rel as Rel, p.nvr as nvr, p.Summary as Summary, r.repo as repo, p.Arch as Arch FROM Files  LEFT JOIN Packages AS p ON (Files.rpm_id=p.rpm_id) LEFT JOIN Distribution AS r ON (p.rpm_id=r.rpm_id) where p.Arch!='src' and p.Name LIKE '" . $this->db->escape_str($searchTerm) . "%' order by p.Name asc, repo, p.Version desc, p.Rel desc ";
            break;
            case "provides":
                $sql = "SELECT DISTINCT p.Name as Name, p.rpm_id as rpm_id, p.build_id as build_id, p.Version as Version , p.Rel as Rel, p.nvr as nvr, p.Summary as Summary, r.repo as repo, p.Arch as Arch FROM Provides LEFT JOIN Packages AS p ON (Provides.rpm_id=p.rpm_id) LEFT JOIN Distribution AS r ON (p.rpm_id=r.rpm_id) where p.Arch!='src' and Provides.Resource LIKE '" . $this->db->escape_str($searchTerm) . "%' " . $hide_clause . " order by p.Name asc, repo, p.Version desc, p.Rel desc";
            break;
            case "requires":
                $sql = "SELECT DISTINCT p.Name as Name, p.rpm_id as rpm_id, p.build_id as build_id, p.Version as Version , p.Rel as Rel, p.nvr as nvr, p.Summary as Summary, r.repo as repo, p.Arch as Arch FROM Requires LEFT JOIN Packages AS p ON (Requires.rpm_id=p.rpm_id) LEFT JOIN Distribution AS r ON (p.rpm_id=r.rpm_id) where p.Arch!='src' and Requires.Resource LIKE '" . $this->db->escape_str($searchTerm) . "%' " . $hide_clause . " order by p.Name asc, repo, p.Version desc, p.Rel desc";
            break;
            case "description":
                $sql = "SELECT DISTINCT p.Name as Name, p.rpm_id as rpm_id, p.build_id as build_id, p.Version as Version , p.Rel as Rel, p.nvr as nvr, p.Summary as Summary, r.repo as repo, p.Arch as Arch FROM Packages AS p LEFT JOIN Distribution AS r ON (p.rpm_id=r.rpm_id) where p.Arch!='src' and p.Description LIKE '%" . $this->db->escape_str($searchTerm) . "%' " . $hide_clause . " order by p.Name asc, repo, p.Version desc, p.Rel desc";
            break;
            case "summary":
                $sql = "SELECT DISTINCT p.Name as Name, p.rpm_id as rpm_id, p.build_id as build_id, p.Version as Version , p.Rel as Rel, p.nvr as nvr, p.Summary as Summary, r.repo as repo, p.Arch as Arch FROM Packages AS p LEFT JOIN Distribution AS r ON (p.rpm_id=r.rpm_id) where p.Arch!='src' and p.Summary LIKE '%" . $this->db->escape_str($searchTerm) . "%' " . $hide_clause . " order by p.Name asc, repo, p.Version desc, p.Rel desc";
            break;
            case "recent":
                $timesearch = time() - 60 * 60 * 24 * 7;
            $sql = " SELECT DISTINCT p.Name as Name, p.rpm_id as rpm_id, p.build_id as build_id, p.Version as Version, p.Rel as Rel, p.nvr as nvr, p.Summary as Summary, p.Arch as Arch, r.repo as repo, p.Date as Date FROM Packages AS p LEFT JOIN Distribution AS r ON (p.rpm_id=r.rpm_id) where p.Arch!='src' and Date > ". $timesearch ." " . $hide_clause . " ORDER BY Name, repo, Version DESC, p.Rel desc";
            break;
        }



        //if we want results from both versions of centos, run them both recursively, and return the combined results
        if(strcmp($centos_version, "both") ==0){
            $result_5 = $this->SearchPackages($searchTerm,$searchType,$user,'5');
            $result_6 = $this->SearchPackages($searchTerm,$searchType,$user,'6');
            if ($result_5 == NULL){$result_5 = array();};
            if ($result_6 == NULL){$result_6 = array();};
            $total_result = array_merge($result_5,$result_6);
            if (empty($total_result)){
                return null;
            }else{
                return $total_result;
            }

        }elseif( strcmp($centos_version , "6") == 0){
            $query = $this->db_centos6->query($sql); 
        }else{
            $query = $this->db->query($sql); 
        }

        if ($query->num_rows() > 0) 
        {
            foreach ($query->result() as $function_info) 
            {
                $function_info->Archs = array($function_info->Arch);
                $function_info->Centos_Version= $centos_version;
                $output[] =  $function_info;
            }
            return $output;
        } 
        else 
        {
            return null;
        }
    }

    function GetNVR($id, $centos_version='5')
    {
        $sql = "select nvr from Packages where rpm_id = " . $id;
        if ($centos_version === '6'){
            $query = $this->db_centos6->query($sql);
        }else{
            $query = $this->db->query($sql);
        }
        $nvr = "";
        if ($query->num_rows() > 0)
        {
            $result = $query->result();
            $nvr = $result[0]->nvr;
        }
        return $nvr;
    }

    function QueueInfo($queuelist)
    {
        $QResult = new StdClass;

        $queue_sql = "select distinct p.build_id as build_id, p.build_name as build_name, p.Version as Version, p.Rel as Rel, p.SRCRPM as SRCRPM, r.repo as repo from Packages as p left join Distribution as r on (p.build_id = r.build_id) where p.build_id in (" . implode($queuelist, ", ") . ") order by build_name asc";
        $queue_query = $this->db->query($queue_sql);
        if ($queue_query->num_rows() > 0)
            $QResult->Builds = $queue_query->result();
        else
            $QResult->Builds = null;

        $rpmlist_sql = "select distinct nvr, Arch, rpm_id from Packages where build_id in (" . implode($queuelist, ", ") . ") order by nvr asc";
        $rpmlist_query = $this->db->query($rpmlist_sql);
        if ($rpmlist_query->num_rows() > 0)
            $QResult->RPMList = $rpmlist_query->result();
        else
            $QResult->RPMList = null;

        return $QResult;
    }

    function FileInfo($rpmid, $filepath, $centos_version='5')
    {
        $QResult = new StdClass; 
        $file_sql = "select * from Files where rpm_id=" . $rpmid . " and Path='" . $filepath . "'";
        if($centos_version ==="5"){
            $file_query = $this->db->query($file_sql);
        }else{
            $file_query = $this->db_centos6->query($file_sql);
        }
        if ($file_query->num_rows() > 0)
        {
            $QResult = $file_query->result();
        }
        return $QResult;
    }

    function SRCRPMs($queuelist, $centos_version='5')
    {
        $srpms_sql = "select distinct SRCRPM from Packages where build_id in (" . implode($queuelist, ", ") . ") order by build_name asc";
        if($centos_version ==='6'){
            $srpms_query = $this->db_centos6->query($srpms_sql);
        }else{
            $srpms_query = $this->db->query($srpms_sql);
        }
        if ($srpms_query->num_rows() > 0){
            $QResult->SRPMs = $srpms_query->result();
        }else{
            $QResult->SRPMs = null;
        }
        return $QResult;
    }

    function SearchPackage($id, $user = False, $centos_version='5')
    {

        if($centos_version === '6'){
            $function_db = $this->db_centos6;

        }else{
            $function_db = $this->db;	
        }

        $QResult = new StdClass;
        $hide_clause = "";
        if ($user == FALSE)
        {
            $dontpublishrepos = $this->config["repositories"]["dontpublishrepos"];
            $hide_clause = "and NOT repo='" . $dontpublishrepos . "'";
        }
        $pkg_sql = "select p.*, r.repo as repo from Packages as p inner join Distribution as r on (r.rpm_id=p.rpm_id) where p.rpm_id='". $id . "' " . $hide_clause . " order by p.Name asc, p.Version desc";
        $pkg_query = $function_db->query($pkg_sql); 
        if ($pkg_query->num_rows() > 0) 
            $QResult->Pkg = $pkg_query->result();
        else
            $QResult->Pkg = null;

        $pkg_info = $QResult->Pkg[0]; // FIXME: what if it is null?
        $clog_sql = "select * from SpecChangeLogs where rpm_id = " . $pkg_info->rpm_id . " order by Date desc, Author desc";
        $clog_query = $function_db->query($clog_sql);
        if ($clog_query->num_rows() > 0)
            $QResult->Clog = $clog_query->result();
        else
            $QResult->Clog = null;

        $swclog_sql = "select * from SoftwareChangeLogs where build_id = " . $pkg_info->build_id;
        $swclog_query = $function_db->query($swclog_sql);
        if ($swclog_query->num_rows() > 0)
        {
            $tmp = $swclog_query->result();
            $QResult->SWClog = $tmp[0];
        }
        else
            $QResult->SWClog = null;

        $archs_sql = "select Arch, rpm_id, srpm_id from Packages where Arch!='src' and build_id = " . $pkg_info->build_id . " and Name = '" . $pkg_info->Name . "'";
        $archs_query = $function_db->query($archs_sql);
        if ($archs_query->num_rows() > 0)
            $QResult->Archs = $archs_query->result();
        else
            $QResult->Archs = null;
        $id = $QResult->Archs[0]->rpm_id; // FIXME: what if it is null?
        $srpm_id = $QResult->Archs[0]->srpm_id; // FIXME: what if it is null?

        foreach ($QResult->Archs as $item)
            if ($item->Arch == $this->config["repositories"]["arch_display"])
                $id = $item->rpm_id;

        $srcfiles_sql = "select f.Path, f.Size, f.Digest from Packages as p inner join Files as f on (f.rpm_id=p.rpm_id) where p.rpm_id='". $srpm_id . "'";
        $srcfiles_query = $function_db->query($srcfiles_sql);
        if ($srcfiles_query->num_rows() > 0)
            $QResult->SRCFiles = $srcfiles_query->result();
        else
            $QResult->SRCFiles = null;

        $files_sql = "select f.Path, f.Size, f.Digest from Packages as p inner join Files as f on (f.rpm_id=p.rpm_id) where p.rpm_id='". $id . "'";
        $files_query = $function_db->query($files_sql);
        if ($files_query->num_rows() > 0)
            $QResult->Files = $files_query->result();
        else
            $QResult->Files = null;

        $requires_sql = "select r.Resource, r.Flags, r.Version from Packages as p inner join Requires as r on (r.rpm_id=p.rpm_id) where p.rpm_id='". $id . "'";
        $requires_query = $function_db->query($requires_sql);
        if ($requires_query->num_rows() > 0)
            $QResult->Requires = $requires_query->result();
        else
            $QResult->Requires = null;

        $provides_sql = "select r.Resource, r.Flags, r.Version from Packages as p inner join Provides as r on (r.rpm_id=p.rpm_id) where p.rpm_id='". $id . "'";
        $provides_query = $function_db->query($provides_sql);
        if ($provides_query->num_rows() > 0)
            $QResult->Provides = $provides_query->result();
        else
            $QResult->Provides = null;

        $obsoletes_sql = "select r.Resource, r.Flags, r.Version from Packages as p inner join Obsoletes as r on (r.rpm_id=p.rpm_id) where p.rpm_id='". $id . "'";
        $obsoletes_query = $function_db->query($obsoletes_sql);
        if ($obsoletes_query->num_rows() > 0)
            $QResult->Obsoletes = $obsoletes_query->result();
        else
            $QResult->Obsoletes = null;

        $conflicts_sql = "select r.Resource, r.Flags, r.Version from Packages as p inner join Conflicts as r on (r.rpm_id=p.rpm_id) where p.rpm_id='". $id . "'";
        $conflicts_query = $function_db->query($conflicts_sql);
        if ($conflicts_query->num_rows() > 0)
            $QResult->Conflicts = $conflicts_query->result();
        else
            $QResult->Conflicts = null;

        return $QResult;
    }
}
?>
