<?php
class Application extends Controller {

	function Application()
	{
		parent::Controller();
		$this->load->model('search_model');
		$this->output->cache(120);
	}
	
	function index()
	{
		$data['user'] = $this->getUser();
		$data['title'] = $this->title;
		$data['search_results'] = $this->search_model->SearchPackages("", "recent", $data['user']);
		$data['ajax_results'] = $this->search_model->ajaxSearch();
		$data['whereami'] = array();
		$this->load->view('application/index', $data);		
	}

	function search()
		{
		$data['user'] = $this->getUser();
		$data['title'] = $this->title;
		$function_name = $this->input->post('function_name');
		$data['search_results'] = $this->search_model->SearchPackages($function_name, $this->input->post('searchby'), $data['user']);
		$data['ajax_results'] = $this->search_model->ajaxSearch();
		$uriarray = explode("/", $_SERVER["REQUEST_URI"]);
                $uriarray = array_slice($uriarray, 2);
                $uri = implode("/", $uriarray);
                $data['whereami'] = array("<a href='" . site_url() . $uri . "'>Search</a>");
		$this->load->view('application/search', $data);	
		}

	function ajaxSearch()
		{
		$data['title'] = $this->title;
		$function_name = $this->input->post('q');
		$data['search_results'] = $this->search_model->ajaxSearch($function_name);
		$this->load->view('application/ajaxSearch', $data);
		}
}
?>
