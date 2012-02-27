<?php
class Packages extends Controller 
{
    function Packages()
    {
        parent::Controller();
        $this->load->model('search_model');
        $this->output->cache(120);
    }

    function index ()
    {
        $data['title'] = $this->title;
        $data['extraHeadContent'] = '<script type="text/javascript" src="' . base_url() . 'js/function_search.js"></script>';
        $data['user'] = $this->getUser();
        $centos_version= $this->uri->segment(4,0);
        if( ! (isset($centos_version) && is_numeric($centos_version))){
            $centos_version = "5";
        }
        $QResult = $this->search_model->SearchPackage($this->uri->segment(3, 0), $data['user'], $centos_version);
        if ($QResult->Pkg)
        {
            $repos=array();
            foreach ($QResult->Pkg as $function_info)
            {
                $repos[] = $function_info->repo;
            }
            $data['repos'] = $repos;

            $farray = $QResult->Pkg;
            $data['pkg_info'] = $farray[0];


            if ($this->uri->segment(4,0) === "getfile")
            {
                $chars = preg_split('/getfile/', $this->uri->uri_string(), -1, PREG_SPLIT_OFFSET_CAPTURE);
                $data['filepath'] = $chars[1][0];

                if($QResult->Pkg[0]->srpm_id == $this->uri->segment(3,0))
                    $FileInfoResult = $this->search_model->FileInfo($this->uri->segment(3, 0),
                            substr($data['filepath'],1));
                else
                    $FileInfoResult = $this->search_model->FileInfo($this->uri->segment(3, 0),
                            $data['filepath']);

                $data['fileflags'] = $FileInfoResult[0]->Flags;
                $data['filesize'] = $FileInfoResult[0]->Size;

                $this->load->view('application/packages', $data);
                return;
            }

            $data['clog_info'] = $QResult->Clog;
            if ($QResult->SWClog)
            {
                $QResult->SWClog->Text =  explode("\n", $QResult->SWClog->Text);
                $data['swclog_info'] = $QResult->SWClog;
            }
            else
                $data['swclog_info'] = False;

            $arch_info = array();
            $archs_results = $QResult->Archs;
            foreach ($archs_results as $item)
                $arch_info[] = $item->Arch;
            sort($arch_info);
            $data['arch_info'] = $arch_info;

            $data['Files'] = $QResult->Files;
            $data['SRCFiles'] = $QResult->SRCFiles;
            $data['Requires'] = $QResult->Requires;
            $data['Provides'] = $QResult->Provides;
            $data['Obsoletes'] = $QResult->Obsoletes;
            $data['Conflicts'] = $QResult->Conflicts;

        }
        else
            $data['pkg_info'] = NULL;

        $mynvr = $this->search_model->GetNVR($this->uri->segment(3, 0),$centos_version);
        $myletter = $mynvr[0];
        $uriarray = explode("/", $_SERVER["REQUEST_URI"]);
        $uriarray = array_slice($uriarray, 2);
        $uri = implode("/", $uriarray);
        $data['whereami'] = array("<a href='" . site_url() . "index.php/letters/index/" . $myletter . "'>" . strtoupper($myletter) . "</a>",
                "<a href='" . site_url() . $uri . "'>" . $mynvr ."</a>");
        $data['ajax_results'] = $this->search_model->ajaxSearch();
        $this->load->view('application/packages', $data);
    }
}
?>
