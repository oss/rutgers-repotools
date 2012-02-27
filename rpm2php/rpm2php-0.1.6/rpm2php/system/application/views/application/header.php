	<script type="text/javascript"> 
		var packages = [
		<?= 
			$ajax_results;
		?>
		];
		$(document).ready(function(){
			$("#function_name").autocomplete(packages, {
				matchContains: true,
				extraParams: {searchby: 'name'},
				minChars: 2,
				selectFirst: false
			});
	  	});
	</script>
	<?php
		if (isset($extraHeadContent)) {
			echo $extraHeadContent;
		}
	?>
	<script type="text/javascript" src="<?=  base_url() ?>js/js_tooltips.js"></script>
	</head>
	<body>
		<div id="header">
	        <div id="seal"></div>
	        <div id="logo"><a href="http://www.rutgers.edu"><img alt="logo" src="<?= site_url('img/logo.png'); ?>" /></a></div>
	        <div id="listmenu">
	            <ul>
	                <li><a href="http://webmail.rutgers.edu/">Webmail</a></li>
	                <li><a href="http://mailman.rutgers.edu/">Mailman</a></li>
	                <li><a href="https://rams.rutgers.edu/">RAMS</a></li>
	                <li><a href="#">More...</a>
	                    <ul>
	                        <li><a href="https://rats.rutgers.edu">RATS</a></li>
	                        <li><a href="https://rim.rutgers.edu/jwchat/">RIM</a></li>
	                    </ul>
	                </li>
	            </ul>
	        </div>
            <div id="search">
                <form method="get" action="http://www.google.com/u/rutgerz" id="gs">
 					<fieldset>
	                    <input type="hidden" name="hl" value="en" />
	                    <input type="hidden" name="lr" value="" />
	                    <input type="hidden" name="ie" value="ISO-8859-1" />
	                    <label for="q">Search: </label><input type="text" id="q" name="q" size="10" maxlength="2048" value="" />
    					<input id="go_button" type="image" src="<?= site_url('img/gobutton.gif'); ?>" alt="Submit button" />
					</fieldset>
				</form>
            </div>
	        <div id="link_line">
	            <a href="http://css.rutgers.edu/">CSS Home</a> | <a href="http://www.rutgers.edu/">Rutgers Home</a> | <a href="http://search.rutgers.edu/">Search</a>
	        </div>
</div>