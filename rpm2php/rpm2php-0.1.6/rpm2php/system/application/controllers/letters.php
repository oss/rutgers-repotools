<?php
class Letters extends Controller 
{
  function Letters()
  {
    parent::Controller();
    $this->load->model('search_model');
    $this->output->cache(120);
  }
  function index ()
  {
    $data['user'] = $this->getUser();
    $data['title'] = $this->title;
    $data['extraHeadContent'] = '<script type="text/javascript" src="' . base_url() . 'js/function_search.js"></script>';
    $myletter = $this->uri->segment(3, 0);
    $data['search_results'] = $this->search_model->SearchPackages($myletter, "letter", $data['user']);
    $data['whereami'] = array("<a href='" . site_url() . "index.php/letters/index/" . $myletter . "'>" . strtoupper($myletter) . "</a>");
    $data['ajax_results'] = $this->search_model->ajaxSearch();
    $this->load->view('application/letters', $data);
  }
}
?>