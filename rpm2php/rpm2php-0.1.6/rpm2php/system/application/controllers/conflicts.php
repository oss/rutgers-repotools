<?php
class Conflicts extends Controller 
{
  
  function Conflicts()
  {
    parent::Controller();
    $this->load->model('search_model');
    $this->output->cache(120);
  }
  
  function index()
  {
    $data['user'] = $this->getUser();
    $data['title'] = $this->title;
    $data['search_results'] = $this->search_model->SearchPackages($this->uri->segment(3, 0), "provides", $data['user']);
    $data['ajax_results'] = $this->search_model->ajaxSearch();
    $uriarray = explode("/", $_SERVER["REQUEST_URI"]);
    $uriarray = array_slice($uriarray, 2);
    $uri = implode("/", $uriarray);
    $data['whereami'] = array("<a href='" . site_url() . $uri . "'>Search</a>");
    $this->load->view('application/conflicts', $data);		
  }
}
?>