		<div id="searchForm">
			<form id="function_search_form" method="post" action="<?=site_url('index.php/application/search');?>">
				<fieldset>
					<label for="searchby">Search by</label>
					<select name="searchby" id="searchby">
						<option value="name" >Name</option>
						<option value="file" > File</option>
						<option value="provides" >Provides</option>
						<option value="requires" >Requires</option>
						<option value="description" >Description</option>
						<option value="summary" >Summary</option>
					</select>
			        <input type="text" name="function_name" id="function_name" />
					<input type="image" src="<?= site_url('img/search.png'); ?>" value="search" id="search_button" />
			<!--			</br>
		<label for="centos_version">in</label>
					<select name="centos_version" id="centos_version">
						<option value="5" >CentOS 5</option>
						<option value="6" >CentOS 6</option>
						<option value="both" >CentOS 5 & 6</option>
					</select>
	-->

				</fieldset>
		    </form>
			<span class="letters">
				<a href="<?= site_url('index.php/letters/index/a'); ?>">A</a> | 
				<a href="<?= site_url('index.php/letters/index/b'); ?>">B</a> | 
				<a href="<?= site_url('index.php/letters/index/c'); ?>">C</a> | 
				<a href="<?= site_url('index.php/letters/index/d'); ?>">D</a> | 
				<a href="<?= site_url('index.php/letters/index/e'); ?>">E</a> | 
				<a href="<?= site_url('index.php/letters/index/f'); ?>">F</a> | 
				<a href="<?= site_url('index.php/letters/index/g'); ?>">G</a> | 
				<a href="<?= site_url('index.php/letters/index/h'); ?>">H</a> | 
				<a href="<?= site_url('index.php/letters/index/i'); ?>">I</a> | 
				<a href="<?= site_url('index.php/letters/index/j'); ?>">J</a> | 
				<a href="<?= site_url('index.php/letters/index/k'); ?>">K</a> | 
				<a href="<?= site_url('index.php/letters/index/l'); ?>">L</a> | 
				<a href="<?= site_url('index.php/letters/index/m'); ?>">M</a> | 
				<a href="<?= site_url('index.php/letters/index/n'); ?>">N</a> | 
				<a href="<?= site_url('index.php/letters/index/o'); ?>">O</a> | 
				<a href="<?= site_url('index.php/letters/index/p'); ?>">P</a> | 
				<a href="<?= site_url('index.php/letters/index/q'); ?>">Q</a> | 
				<a href="<?= site_url('index.php/letters/index/r'); ?>">R</a> | 
				<a href="<?= site_url('index.php/letters/index/s'); ?>">S</a> | 
				<a href="<?= site_url('index.php/letters/index/t'); ?>">T</a> | 
				<a href="<?= site_url('index.php/letters/index/u'); ?>">U</a> | 
				<a href="<?= site_url('index.php/letters/index/v'); ?>">V</a> | 
				<a href="<?= site_url('index.php/letters/index/w'); ?>">W</a> | 
				<a href="<?= site_url('index.php/letters/index/x'); ?>">X</a> | 
				<a href="<?= site_url('index.php/letters/index/y'); ?>">Y</a> | 
				<a href="<?= site_url('index.php/letters/index/z'); ?>">Z</a>
			</span>
		</div>
