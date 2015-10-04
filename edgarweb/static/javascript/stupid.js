function start_long_task(tick) {
    // add task status elements

    div = $('<div id="progress"><div></div><div>0%</div><div>...</div><div>&nbsp;</div></div><hr>');
    $('#progress').append(div); //must be hashtag id string
    // create a progress bar
    var nanobar = new Nanobar({
	bg: '#44f',
	target: div[0].childNodes[0]
    });
    // send ajax POST request to start background job
    $.ajax({
	type: 'POST',
	url:  '/getdataframe/' + tick,
	success: function(data, status, request) {
	    status_url = request.getResponseHeader('Location');
	    update_progress(status_url, nanobar, div[0]);
	},
	error: function() {
	    alert('Unexpected error');
	}
    });
    return false; //hot tip this makes sure form action doesn't return to /datadisplay
}
function update_progress(status_url, nanobar, status_div) {
    // send GET request to status URL
    $.getJSON(status_url, function(data) {
	//update UI
	percent = parseInt(data['percent']);
	if (data['state'] != 'PENDING' && data['state'] != 'PROGRESS') {
	    if ('result' in data) {
		//show result
		$(status_div.childNodes[2]).text('Done');
		$(status_div.childNodes[3]).text('Result: ' + data['result']);

		//is this ghetto I copy from stack exchange, to redirect fillout a
		//hidden form then submit it so that we load datadisplay in POST
		//then we play with dataframe
		var url = '/datadisplay';
		var form = $('<form action="' + url + '" method="post">' +
			     '<input type="text" name="api_url" value="' + 'aho' + '" />' +
			     '</form>');
		$('body').append(form);
		form.submit();
	    }
	    else {
		// something bad happened
		$(status_div.childNodes[3]).text('Result: ' + data['state']);
	    }
	}
	else {
	    // rerun in 1.0 seconds
	    nanobar.go(percent);
	    $(status_div.childNodes[1]).text(percent + '%');
	    $(status_div.childNodes[2]).text(data['state'] + ' : ' + data['message']);

	    setTimeout(function() {
		update_progress(status_url, nanobar, status_div);
	    }, 1000);
	}
    });
}

// is this jQuery? I know so little...
$(document).ready(function() {
    $('#boke').click(function() {
	if(!$('#baka').val()) { window.alert("You must supply S&P ticker"); }
	else {
	    this.disabled = true;
	    start_long_task($('#baka').val());
	}
    });
});
