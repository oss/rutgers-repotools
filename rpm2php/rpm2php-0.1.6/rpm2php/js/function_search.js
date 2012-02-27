window.onload = function () 
	{
	if (typeof($F) !== 'undefined') {
		var passSearch = "searchby=" + $F('searchby');
		new Ajax.Autocompleter("function_name", "autocomplete_choices", base_url + "application/ajaxSearch/", 
			{
			minChars: 2,
			parameters: passSearch
			});
		
		$('function_search_form').onsubmit = function()
			{
			inline_results();
			return false;
			}
		}
	}

function inline_results() 
	{
	if($F)
		{
		new Ajax.Updater ('function_description', base_url+'application/search', {method:'post', postBody:'description=true&function_name='+$F('function_name')+'&searchby='+$F('searchby')});
		new Effect.Appear('function_description');
		}
	}